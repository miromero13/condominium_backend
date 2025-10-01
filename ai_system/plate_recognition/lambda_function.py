import json
import boto3
import urllib.parse
from datetime import datetime

# Clientes AWS
rekognition = boto3.client('rekognition')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Función Lambda que se ejecuta automáticamente cuando se sube una imagen a S3.
    Detecta placas usando Rekognition y envía notificaciones via SNS.
    """
    
    try:
        # Extraer información del evento S3
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        print(f"Procesando imagen: {key} desde bucket: {bucket}")
        
        # Llamar a Rekognition para detectar texto (placas)
        response = rekognition.detect_text(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Procesar resultados de detección
        placas_detectadas = []
        
        for text_detection in response['TextDetections']:
            if text_detection['Type'] == 'LINE':
                detected_text = text_detection['DetectedText']
                confidence = text_detection['Confidence']
                
                # Filtrar solo texto que parezca placa (6-8 caracteres, alfanumérico)
                if len(detected_text) >= 6 and len(detected_text) <= 8 and detected_text.replace('-', '').replace(' ', '').isalnum():
                    placas_detectadas.append({
                        'placa': detected_text.upper().replace(' ', '').replace('-', ''),
                        'confianza': round(confidence, 2),
                        'coordenadas': text_detection.get('Geometry', {})
                    })
        
        # Preparar mensaje para SNS
        if placas_detectadas:
            mensaje = {
                'tipo_evento': 'DETECCION_PLACA',
                'timestamp': datetime.utcnow().isoformat(),
                'imagen_s3': f"s3://{bucket}/{key}",
                'placas_detectadas': placas_detectadas,
                'total_placas': len(placas_detectadas)
            }
            
            # Enviar notificación via SNS
            sns_response = sns.publish(
                TopicArn='arn:aws:sns:us-east-1:570082719491:SmartCondominio-AI-Alerts',
                Message=json.dumps(mensaje, indent=2),
                Subject=f'SmartCondominio: {len(placas_detectadas)} placa(s) detectada(s)'
            )
            
            print(f"Notificación SNS enviada: {sns_response['MessageId']}")
            
        else:
            # No se detectaron placas
            mensaje_error = {
                'tipo_evento': 'SIN_DETECCION',
                'timestamp': datetime.utcnow().isoformat(),
                'imagen_s3': f"s3://{bucket}/{key}",
                'mensaje': 'No se detectaron placas en la imagen'
            }
            
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:570082719491:SmartCondominio-AI-Alerts',
                Message=json.dumps(mensaje_error, indent=2),
                Subject='SmartCondominio: Sin detección de placas'
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Procesamiento completado',
                'placas_detectadas': len(placas_detectadas),
                'imagen_procesada': key
            })
        }
        
    except Exception as e:
        print(f"Error procesando imagen: {str(e)}")
        
        # Enviar notificación de error via SNS
        error_message = {
            'tipo_evento': 'ERROR_PROCESAMIENTO',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'imagen': key if 'key' in locals() else 'desconocida'
        }
        
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:570082719491:SmartCondominio-AI-Alerts',
            Message=json.dumps(error_message, indent=2),
            Subject='SmartCondominio: Error en procesamiento IA'
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
