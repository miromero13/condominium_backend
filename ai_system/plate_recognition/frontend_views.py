from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from property.models import Vehicle
import boto3
import base64
import uuid
import time
import re
from config.response import response

@api_view(['POST'])
@permission_classes([AllowAny])
def detect_plate_frontend(request):
    """
    Endpoint simplificado para detectar placas desde el frontend
    Acepta tanto archivos como base64 de cámara
    """
    try:
        print(f"🔍 [DEBUG] detect_plate_frontend called with data: {list(request.data.keys())}")
        print(f"🔍 [DEBUG] FILES: {list(request.FILES.keys())}")
        start_time = time.time()
        
        # Obtener imagen del request
        if 'image' in request.FILES:
            print(f"🔍 [DEBUG] Processing file upload")
            # Upload de archivo
            image_file = request.FILES['image']
            source = request.data.get('source', 'upload')
            print(f"🔍 [DEBUG] File: {image_file.name}, Size: {image_file.size}, Source: {source}")
            
            # Generar nombre único para el archivo
            file_extension = image_file.name.split('.')[-1]
            filename = f"plate_detection/{uuid.uuid4()}.{file_extension}"
            
            # Subir a S3
            try:
                print(f"🔍 [DEBUG] Uploading to S3...")
                s3_client = boto3.client('s3')
                bucket_name = 'smartcondominio-ai-nataly-2025'
                s3_client.upload_fileobj(image_file, bucket_name, filename)
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
                print(f"🔍 [DEBUG] S3 upload successful: {s3_url}")
            except Exception as e:
                print(f"❌ [ERROR] S3 upload failed: {str(e)}")
                return response(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error subiendo imagen a S3",
                    error=str(e)
                )
        
        elif 'image_base64' in request.data:
            # Base64 de cámara
            image_base64 = request.data['image_base64']
            source = request.data.get('source', 'camera')
            print(f"🔍 [DEBUG] image_base64 (first 100): {image_base64[:100]}")
            # Decodificar base64
            try:
                if ',' in image_base64:
                    header, data = image_base64.split(',', 1)
                    print(f"🔍 [DEBUG] base64 header: {header}")
                else:
                    data = image_base64
                    print(f"🔍 [DEBUG] base64 header: (none, pure base64)")
                image_data = base64.b64decode(data)
                print(f"🔍 [DEBUG] Decoded image_data length: {len(image_data)} bytes")
                # Generar nombre único
                filename = f"plate_detection/{uuid.uuid4()}.jpg"
                # Subir a S3
                s3_client = boto3.client('s3')
                bucket_name = 'smartcondominio-ai-nataly-2025'
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=filename,
                    Body=image_data,
                    ContentType='image/jpeg'
                )
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
            except Exception as e:
                import traceback
                print(f"❌ [ERROR] image_base64 exception: {str(e)}")
                print(f"❌ [ERROR] Traceback: {traceback.format_exc()}")
                return response(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error procesando imagen base64",
                    error=str(e)
                )
        else:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Se requiere 'image' (archivo) o 'image_base64' (cámara)"
            )
        
        # Usar AWS Rekognition para detectar texto
        try:
            print(f"🔍 [DEBUG] Starting AWS Rekognition...")
            rekognition_client = boto3.client('rekognition')
            
            print(f"🔍 [DEBUG] Calling detect_text on {bucket_name}/{filename}")
            response_rekognition = rekognition_client.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': filename
                    }
                }
            )
            print(f"🔍 [DEBUG] Rekognition response received")
            
            # Procesar respuesta de Rekognition
            mejor_placa = None
            confianza_maxima = 0
            
            print(f"🔍 [DEBUG] Processing {len(response_rekognition['TextDetections'])} text detections...")
            for text_detection in response_rekognition['TextDetections']:
                if text_detection['Type'] == 'LINE':
                    texto = text_detection['DetectedText'].strip().upper()
                    confianza = text_detection['Confidence']
                    print(f"🔍 [DEBUG] Found text: '{texto}' (confidence: {confianza:.2f})")
                    
                    # Validar formato de placa (simplificado)
                    is_valid = is_valid_plate_format(texto)
                    print(f"🔍 [DEBUG] Is valid plate format: {is_valid}")
                    
                    if is_valid and confianza > confianza_maxima:
                        mejor_placa = texto
                        confianza_maxima = confianza
                        print(f"🔍 [DEBUG] New best plate: {mejor_placa} (confidence: {confianza_maxima:.2f})")
            
            print(f"🔍 [DEBUG] Final best plate: {mejor_placa}")
            
            # Verificar si la placa está registrada
            vehiculo_autorizado = False
            vehicle_info = None
            placa_normalizada = None
            
            if mejor_placa:
                # Normalizar placa para búsqueda (remover espacios, guiones, puntos)
                placa_normalizada = mejor_placa.replace(' ', '').replace('-', '').replace('.', '').upper()
                print(f"🔍 [DEBUG] Looking up plate '{mejor_placa}' -> normalized: '{placa_normalizada}' in database...")
                
                try:
                    # Buscar por placa normalizada
                    vehicle = Vehicle.objects.select_related('property').get(
                        plate=placa_normalizada
                    )
                    print(f"🔍 [DEBUG] Vehicle found in database: {vehicle.plate} - {vehicle.brand} {vehicle.model}")
                    vehiculo_autorizado = True
                    vehicle_info = {
                        "id": str(vehicle.id),
                        "plate": vehicle.plate,        
                        "brand": vehicle.brand,        
                        "model": vehicle.model,       
                        "color": vehicle.color,
                        "type_vehicle": vehicle.type_vehicle,  
                        "property_name": vehicle.property.name if vehicle.property else "Sin propiedad"
                    }
                except Vehicle.DoesNotExist:
                    print(f"🔍 [DEBUG] Vehicle not found in database")
                    vehiculo_autorizado = False
            
            # Calcular tiempo de procesamiento
            tiempo_procesamiento = round(time.time() - start_time, 2)
            
            # Crear registro en EventoAI para historial
            from ai_system.models import EventoAI
            if mejor_placa and confianza_maxima > 0:
                EventoAI.objects.create(
                    tipo='deteccion_placa_frontend',
                    confianza=confianza_maxima / 100,  # Guardar como decimal
                    descripcion=f"Detección desde frontend: {mejor_placa} ({'autorizada' if vehiculo_autorizado else 'no autorizada'})",
                    imagen_s3_url=s3_url,
                    fuente_deteccion=source,
                    datos_adicionales={
                        'plate_detected_raw': mejor_placa,  # Como la detectó Rekognition
                        'plate_detected_normalized': placa_normalizada,  # Como se busca en BD
                        'authorized_vehicle': vehiculo_autorizado,
                        'processing_time': tiempo_procesamiento,
                        'vehicle_info': vehicle_info
                    }
                )
            
            # Preparar respuesta
            if mejor_placa:
                mensaje = f"Placa detectada: {mejor_placa} (normalizada: {placa_normalizada})"
                if vehiculo_autorizado:
                    mensaje += " - ACCESO AUTORIZADO"
                else:
                    mensaje += " - ACCESO DENEGADO (Vehículo no registrado)"
            else:
                mensaje = "No se detectó ninguna placa válida"
            
            response_data = {
                "plate_detected": mejor_placa,
                "confidence": round(confianza_maxima / 100, 3),  # Convertir a decimal 0.0-1.0
                "authorized_vehicle": vehiculo_autorizado,
                "message": mensaje,
                "processing_time": tiempo_procesamiento,
                "vehicle_info": vehicle_info,
                "s3_url": s3_url
            }
            
            print(f"🔍 [DEBUG] Sending response: authorized_vehicle={vehiculo_autorizado}, confidence={response_data['confidence']}")
            
            return response(
                status_code=status.HTTP_200_OK,
                message="Detección completada",
                data=response_data
            )
            
        except Exception as e:
            print(f"❌ [ERROR] AWS Rekognition error: {str(e)}")
            return response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error en AWS Rekognition",
                error=str(e)
            )
            
    except Exception as e:
        print(f"❌ [ERROR] General server error: {str(e)}")
        import traceback
        print(f"❌ [ERROR] Traceback: {traceback.format_exc()}")
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error interno del servidor",
            error=str(e)
        )


def is_valid_plate_format(text):
    """
    Valida formato básico de placa vehicular
    Acepta patrones variados para diferentes tipos de placas
    """
    if not text or len(text) < 3 or len(text) > 15:
        return False
    
    # Limpiar texto
    cleaned_text = text.strip().replace(' ', '').replace('-', '').replace('.', '')
    
    # Debe tener al menos una letra y un número
    has_letter = bool(re.search(r'[A-Z]', cleaned_text))
    has_number = bool(re.search(r'[0-9]', cleaned_text))
    
    # Si tiene letras y números, es probablemente una placa válida
    # Patrones más permisivos para cubrir formatos diversos:
    patterns = [
        r'^[A-Z]{2,4}[0-9]{2,4}$',        # ABC123, PGMN112
        r'^[A-Z]{1,3}[0-9]{1,4}[A-Z]{1,3}$',  # TN37CS, A123B
        r'^[0-9]{2,4}[A-Z]{2,4}$',        # 123ABC, 497RKP  
        r'^[0-9]{1,3}[A-Z]{1,4}[0-9]{1,3}$',  # 12ABC34
        r'^[A-Z]{1,6}[0-9]{1,6}[A-Z]{0,3}$', # Formatos mixtos variados
    ]
    
    # Si tiene letras y números y no es demasiado largo, probablemente es válida
    return has_letter and has_number and len(cleaned_text) >= 3 and len(cleaned_text) <= 12
