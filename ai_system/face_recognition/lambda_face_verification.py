"""
AWS Lambda para verificación facial en S3 usando Rekognition.
Recibe imagen (base64 o archivo), busca en S3 la carpeta del usuario, compara con las imágenes usando Rekognition.
Si no hay acceso autorizado, puede enviar notificación SNS (comentado para evitar gastos).
"""

import boto3
import base64
import os
import json



# Leer variables de entorno (sin valores por defecto, solo .env)
BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
COLLECTION_ID = os.environ['COLLECTION_ID']
SNS_TOPIC_ARN = os.environ['AWS_SNS_TOPIC_ARN']

rekognition = boto3.client('rekognition')
sns = boto3.client('sns')



def lambda_handler(event, context):
    # Recibe: { 'image_base64': '...' }
    image_base64 = event.get('image_base64')
    if not image_base64:
        return {'statusCode': 400, 'body': 'Falta imagen'}

    # Decodificar imagen
    image_bytes = base64.b64decode(image_base64.split(',')[-1])

    try:
        response = rekognition.search_faces_by_image(
            CollectionId=COLLECTION_ID,
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=85
        )
        matches = response.get('FaceMatches', [])
        if matches:
            face = matches[0]
            external_id = face['Face']['ExternalImageId']
            similarity = face['Similarity']
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'authorized': True,
                    'confidence': similarity,
                    'user_id': external_id,
                    'face_id': face['Face']['FaceId'],
                    'message': f"Match con usuario {external_id}",
                })
            }
        else:
            # Acceso no autorizado
            # Si quieres enviar notificación SNS, descomenta:
            # mensaje = {
            #     'tipo_evento': 'ACCESO_NO_AUTORIZADO',
            #     'timestamp': datetime.utcnow().isoformat(),
            #     'mensaje': 'No se encontró coincidencia en la colección',
            # }
            # sns.publish(
            #     TopicArn=SNS_TOPIC_ARN,
            #     Message=json.dumps(mensaje, indent=2),
            #     Subject='SmartCondominio: Acceso no autorizado'
            # )
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'authorized': False,
                    'confidence': 0,
                    'message': 'No se encontró coincidencia en la colección',
                })
            }
    except Exception as e:
        # Si quieres enviar notificación SNS de error, descomenta:
        # error_message = {
        #     'tipo_evento': 'ERROR_PROCESAMIENTO',
        #     'timestamp': datetime.utcnow().isoformat(),
        #     'error': str(e),
        # }
        # sns.publish(
        #     TopicArn=SNS_TOPIC_ARN,
        #     Message=json.dumps(error_message, indent=2),
        #     Subject='SmartCondominio: Error en verificación facial'
        # )
        return {'statusCode': 500, 'body': str(e)}
