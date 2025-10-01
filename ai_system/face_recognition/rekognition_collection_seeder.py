import boto3
import os
import re

def get_all_face_images(s3_client, bucket_name, prefix):
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    images = []
    for page in page_iterator:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if re.search(r'\.jpe?g$|\.png$', key, re.IGNORECASE):
                images.append(key)
    return images

def main():
    bucket_name = 'smartcondominio-ai-nataly-2025'  # <-- Cambia por tu bucket
    prefix = 'faces/'  # <-- Cambia por el prefijo donde están las carpetas de usuarios
    collection_id = 'smartcondominio-2025-faces'  # <-- Cambia por tu colección

    s3_client = boto3.client('s3')
    rekognition = boto3.client('rekognition')

    images = get_all_face_images(s3_client, bucket_name, prefix)
    print(f'Total imágenes encontradas: {len(images)}')

    count = 0
    for key in images:
        # Extraer user_id de la carpeta (asumiendo faces/<user_id>/imagen.jpg)
        parts = key.split('/')
        if len(parts) < 3:
            continue
        user_id = parts[1]
        try:
            print(f"Agregando {key} a colección con ExternalImageId={user_id}")
            response = rekognition.index_faces(
                CollectionId=collection_id,
                Image={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': key
                    }
                },
                ExternalImageId=user_id,
                DetectionAttributes=['DEFAULT']
            )
            print(f"Faces indexed: {len(response['FaceRecords'])}")
            count += 1
            if count % 10 == 0:
                print(f"Progreso: {count} imágenes indexadas...")
        except Exception as e:
            print(f"Error al indexar {key}: {e}")

if __name__ == '__main__':
    main()
