import os
import cv2
import boto3

def extract_frames_from_video(video_path, output_dir, interval=1):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = 0
    saved = 0
    success, frame = cap.read()
    while success:
        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % int(fps * interval) == 0:
            filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_frame_{saved:04d}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            saved += 1
        success, frame = cap.read()
        count += 1
    cap.release()
    print(f"Extraídos {saved} frames de {video_path}")
    return saved


def index_images_to_rekognition(local_dir, collection_id, external_image_id, region='us-east-1'):
    rekognition = boto3.client('rekognition', region_name=region)
    for fname in os.listdir(local_dir):
        if fname.lower().endswith('.jpg'):
            local_path = os.path.join(local_dir, fname)
            with open(local_path, 'rb') as img_file:
                img_bytes = img_file.read()
            try:
                response = rekognition.index_faces(
                    CollectionId=collection_id,
                    Image={'Bytes': img_bytes},
                    ExternalImageId=external_image_id,
                    DetectionAttributes=['DEFAULT']
                )
                face_ids = [face_record['Face']['FaceId'] for face_record in response.get('FaceRecords', [])]
                print(f"Indexado: {fname} -> FaceIds: {face_ids}")
            except Exception as e:
                print(f"Error indexando {fname}: {e}")


def main():
    video_dir = r'I:\Usuarios\Imágenes\Camera Roll'
    output_dir = r'frames_temp'
    os.makedirs(output_dir, exist_ok=True)
    collection_id = 'smartcondominio-2025-faces'
    external_image_id = 'fbefb9f0-33a5-4057-abbb-ab125f38a175'

    # Extraer frames de todos los videos
    for fname in os.listdir(video_dir):
        if fname.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            video_path = os.path.join(video_dir, fname)
            extract_frames_from_video(video_path, output_dir, interval=1)

    # Indexar todas las imágenes extraídas directamente en Rekognition
    index_images_to_rekognition(output_dir, collection_id, external_image_id)

    print("Proceso completado. Las imágenes han sido indexadas directamente en Rekognition.")

if __name__ == '__main__':
    main()
