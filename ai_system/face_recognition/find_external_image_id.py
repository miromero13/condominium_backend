import boto3

rekognition = boto3.client('rekognition', region_name='us-east-1')
collection_id = 'smartcondominio-2025-faces'
target_external_id = 'fbefb9f0-33a5-4057-abbb-ab125f38a175'

found = False
pagination_token = None

print(f"Buscando ExternalImageId: {target_external_id}")
while True:
    if pagination_token:
        response = rekognition.list_faces(CollectionId=collection_id, MaxResults=50, NextToken=pagination_token)
    else:
        response = rekognition.list_faces(CollectionId=collection_id, MaxResults=50)
    for face in response['Faces']:
        if face.get('ExternalImageId') == target_external_id:
            print(f"ENCONTRADO: FaceId: {face['FaceId']}, ExternalImageId: {face['ExternalImageId']}")
            found = True
    pagination_token = response.get('NextToken')
    if not pagination_token:
        break

if not found:
    print("No se encontró el ExternalImageId en la colección.")