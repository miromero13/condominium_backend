import boto3

# Configuración
region = 'us-east-1'
collection_id = 'smartcondominio-2025-faces'

# Inicializar cliente Rekognition
rekognition = boto3.client('rekognition', region_name=region)

# Listar rostros en la colección
response = rekognition.list_faces(CollectionId=collection_id, MaxResults=50)

print(f"Rostros en la colección '{collection_id}':")
for face in response['Faces']:
    print(f"FaceId: {face['FaceId']}, ExternalImageId: {face.get('ExternalImageId', '')}")

if not response['Faces']:
    print("No hay rostros registrados en la colección.")
