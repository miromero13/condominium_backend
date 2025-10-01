import boto3
import os

# Configuración
region = 'us-east-1'
collection_id = 'smartcondominio-2025-faces'
bucket = 'smartcondominio-ai-nataly-2025'
external_image_id = 'fbefb9f0-33a5-4057-abbb-ab125f38a175'
local_folder = r'D:\1.Usuarios\Nataly\train\n000000'


rekognition = boto3.client('rekognition', region_name=region)
s3 = boto3.client('s3', region_name=region)

# Crear la Collection si no existe
try:
    rekognition.describe_collection(CollectionId=collection_id)
    print(f"La Collection '{collection_id}' ya existe.")
except rekognition.exceptions.ResourceNotFoundException:
    print(f"Creando la Collection '{collection_id}'...")
    rekognition.create_collection(CollectionId=collection_id)
    print(f"Collection '{collection_id}' creada.")

# Subir e indexar cada imagen en la carpeta
for filename in os.listdir(local_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        local_path = os.path.join(local_folder, filename)
        s3_key = f'faces/{filename}'
        print(f'Subiendo {local_path} a S3 como {s3_key}...')
        s3.upload_file(local_path, bucket, s3_key)
        print(f'Indexando {s3_key} en Rekognition...')
        response = rekognition.index_faces(
            CollectionId=collection_id,
            Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
            ExternalImageId=external_image_id,
            DetectionAttributes=['DEFAULT']
        )
        print(f"Faces indexados: {[face_record['Face']['FaceId'] for face_record in response.get('FaceRecords', [])]}")
print('Proceso completado.')
