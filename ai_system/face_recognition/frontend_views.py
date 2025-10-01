from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import boto3
import base64
import uuid
import time

@api_view(['POST'])
@permission_classes([AllowAny])
def detect_face_frontend(request):
    """
    Endpoint para subir imagen de rostro desde el frontend (archivo o base64)
    Sube la imagen a S3 en faces/ y retorna el estado
    """
    try:
        print(f"🔍 [DEBUG] detect_face_frontend called with data: {list(request.data.keys())}")
        print(f"🔍 [DEBUG] FILES: {list(request.FILES.keys())}")
        start_time = time.time()

        # Obtener imagen del request
        if 'image' in request.FILES:
            print(f"🔍 [DEBUG] Processing file upload")
            image_file = request.FILES['image']
            source = request.data.get('source', 'upload')
            print(f"🔍 [DEBUG] File: {image_file.name}, Size: {image_file.size}, Source: {source}")
            file_extension = image_file.name.split('.')[-1]
            filename = f"faces/{uuid.uuid4()}.{file_extension}"
            try:
                print(f"🔍 [DEBUG] Uploading to S3...")
                s3_client = boto3.client('s3')
                bucket_name = 'smartcondominio-ai-nataly-2025'
                s3_client.upload_fileobj(image_file, bucket_name, filename)
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
                print(f"🔍 [DEBUG] S3 upload successful: {s3_url}")
                return Response({
                    'status': 'uploaded',
                    's3_key': filename,
                    'bucket': bucket_name,
                    's3_url': s3_url
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"❌ [ERROR] S3 upload failed: {str(e)}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif 'image_base64' in request.data:
            image_base64 = request.data['image_base64']
            source = request.data.get('source', 'camera')
            print(f"🔍 [DEBUG] image_base64 (first 100): {image_base64[:100]}")
            try:
                if ',' in image_base64:
                    header, data = image_base64.split(',', 1)
                    print(f"🔍 [DEBUG] base64 header: {header}")
                else:
                    data = image_base64
                    print(f"🔍 [DEBUG] base64 header: (none, pure base64)")
                image_data = base64.b64decode(data)
                print(f"🔍 [DEBUG] Decoded image_data length: {len(image_data)} bytes")
                filename = f"faces/{uuid.uuid4()}.jpg"
                s3_client = boto3.client('s3')
                bucket_name = 'smartcondominio-ai-nataly-2025'
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=filename,
                    Body=image_data,
                    ContentType='image/jpeg'
                )
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
                print(f"🔍 [DEBUG] S3 upload successful: {s3_url}")
                return Response({
                    'status': 'uploaded',
                    's3_key': filename,
                    'bucket': bucket_name,
                    's3_url': s3_url
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"❌ [ERROR] S3 upload failed: {str(e)}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"❌ [ERROR] Unexpected error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)