
import boto3
import base64
import json
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from ai_system.models import EventoAI, Acceso
from ai_system.serializers import EventoAISerializer
from user.models import User
from config.enums import TipoEventoAI, TipoAcceso

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_face(request):
    import logging
    logger = logging.getLogger("face_verification")
    user_id = request.data.get('user_id')
    logger.error(f"[verify_face] user_id: {user_id}")
    """
    Endpoint para verificación facial en vivo.
    Recibe: { 'user_id': '...', 'image_base64': '...' }
    Llama a la función Lambda en AWS para comparar la imagen con la colección de Rekognition.
    Registra EventoAI y Acceso (si corresponde) con descripciones explícitas para auditoría.
    """
    image_base64 = request.data.get('image_base64')
    if not image_base64:
        logger.error("Falta image_base64 en el request")
        return Response({'error': 'Falta image_base64'}, status=status.HTTP_400_BAD_REQUEST)

    # Subir imagen a S3 (faces/)
    import uuid
    s3_client = boto3.client('s3')
    bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'smartcondominio-ai-nataly-2025')
    image_id = str(uuid.uuid4())
    try:
        image_bytes = base64.b64decode(image_base64.split(',')[-1])
    except Exception as e:
        logger.error(f"Error decodificando base64: {str(e)}")
        return Response({'error': 'Error decodificando imagen'}, status=status.HTTP_400_BAD_REQUEST)
    s3_key = f"faces/{image_id}.jpg"
    try:
        s3_client.put_object(Bucket=bucket, Key=s3_key, Body=image_bytes, ContentType='image/jpeg')
        logger.error(f"[verify_face] Imagen subida a S3: {s3_key}")

        # Buscar coincidencias automáticas en la Collection
        rekognition = boto3.client('rekognition')
        collection_id = os.environ.get('COLLECTION_ID', 'smartcondominio-2025-faces')
        try:
            response = rekognition.search_faces_by_image(
                CollectionId=collection_id,
                Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
                MaxFaces=1,
                FaceMatchThreshold=80
            )
            matches = response.get('FaceMatches', [])
            if matches:
                match = matches[0]
                external_id = match['Face'].get('ExternalImageId')
                confidence = min(match['Similarity'], 100.0)
                logger.error(f"[verify_face] Coincidencia encontrada: ExternalImageId={external_id}, Confianza={confidence}")
                # Buscar usuario por external_id
                user_info = None
                try:
                    usuario = User.objects.get(id=external_id)
                    user_info = {
                        'nombre': usuario.name,
                        'email': usuario.email,
                        'telefono': usuario.phone,
                        'rol': usuario.role,
                    }
                except User.DoesNotExist:
                    user_info = None
                return Response({
                    'authorized_person': True,
                    'external_image_id': external_id,
                    'confidence': confidence,
                    'person_info': user_info,
                    's3_key': s3_key,
                    'bucket': bucket
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"[verify_face] No se encontró coincidencia en la Collection")
                return Response({
                    'authorized_person': False,
                    'mensaje': 'Persona no autorizada',
                    's3_key': s3_key,
                    'bucket': bucket
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en search_faces_by_image: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error subiendo imagen a S3: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
