"""
Script OCR optimizado para procesar imágenes YA SUBIDAS a S3

Flujo simplificado:
1. Listar todas las imágenes en S3 bucket 
2. Para cada imagen → AWS Rekognition OCR
3. Extraer placas detectadas
4. Generar JSON limpio para poblar base de datos
5. Estadísticas del procesamiento

Ventajas:
- No sube archivos (ya están en S3)
- Solo procesamiento OCR 
- Muy rápido y eficiente
- Genera archivo listo para seeder Django
"""

import boto3
import json
import re
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class S3OCRProcessor:
    def __init__(self, bucket_name='smartcondominio-ai-nataly-2025', folder_prefix='dataset-seeding/'):
        """
        Procesar imágenes que ya están en S3
        
        Args:
            bucket_name: Nombre del bucket S3
            folder_prefix: Carpeta donde están las imágenes
        """
        self.bucket_name = bucket_name
        self.folder_prefix = folder_prefix
        
        # Clientes AWS
        try:
            self.s3_client = boto3.client('s3')
            self.rekognition_client = boto3.client('rekognition')
            logger.info("✅ Conexión AWS establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a AWS: {e}")
            raise
        
        # Carpeta de resultados
        self.results_dir = Path(__file__).parent / 'results'
        self.results_dir.mkdir(exist_ok=True)
        
        # Estadísticas
        self.stats = {
            'imagenes_procesadas': 0,
            'placas_detectadas': 0,
            'placas_validas': 0,
            'errores': 0,
            'inicio': datetime.now()
        }
    
    def listar_imagenes_s3(self):
        """
        Obtener lista de todas las imágenes en S3
        """
        logger.info(f"🔍 Buscando imágenes en s3://{self.bucket_name}/{self.folder_prefix}")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.folder_prefix
            )
            
            if 'Contents' not in response:
                logger.warning("❌ No se encontraron archivos en S3")
                return []
            
            # Filtrar solo imágenes
            imagenes = []
            for obj in response['Contents']:
                key = obj['Key']
                if key.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    imagenes.append(key)
            
            logger.info(f"📊 Encontradas {len(imagenes)} imágenes en S3")
            return imagenes
            
        except Exception as e:
            logger.error(f"❌ Error listando imágenes S3: {e}")
            return []
    
    def detectar_placa_rekognition(self, imagen_key):
        """
        Usar Rekognition para detectar texto en una imagen de S3
        
        Args:
            imagen_key: Clave de la imagen en S3
            
        Returns:
            Lista de placas detectadas con confianza
        """
        try:
            # Llamar a Rekognition
            response = self.rekognition_client.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': imagen_key
                    }
                }
            )
            
            placas_detectadas = []
            
            # Procesar respuesta
            for detection in response.get('TextDetections', []):
                if detection['Type'] == 'LINE':  # Solo líneas completas
                    texto = detection['DetectedText'].strip()
                    confianza = detection['Confidence']
                    
                    # Filtrar texto que parece placa
                    placa_candidata = self.validar_placa(texto)
                    if placa_candidata and confianza >= 70:  # Mínimo 70% confianza
                        placas_detectadas.append({
                            'placa': placa_candidata,
                            'confianza': round(confianza, 2),
                            'texto_original': texto,
                            'imagen': imagen_key
                        })
            
            return placas_detectadas
            
        except Exception as e:
            logger.error(f"❌ Error procesando {imagen_key}: {e}")
            self.stats['errores'] += 1
            return []
    
    def validar_placa(self, texto):
        """
        Validar y limpiar texto que parece placa vehicular
        
        Args:
            texto: Texto detectado por Rekognition
            
        Returns:
            Placa limpia o None si no es válida
        """
        if not texto:
            return None
        
        # Limpiar texto
        texto_limpio = re.sub(r'[^A-Za-z0-9]', '', texto.upper())
        
        # Validaciones de formato de placa
        if len(texto_limpio) < 5 or len(texto_limpio) > 10:
            return None
        
        # Debe tener al menos algunos números o letras
        if not re.search(r'[A-Z]', texto_limpio) and not re.search(r'[0-9]', texto_limpio):
            return None
        
        # Evitar texto común que no son placas
        texto_excluidos = [
            'STOP', 'TAXI', 'POLICE', 'FIRE', 'RESCUE', 
            'AMBULANCE', 'BUS', 'SCHOOL', 'EMERGENCY', 'BRASIL', 'MERCOSUL'
        ]
        if texto_limpio in texto_excluidos:
            return None
        
        return texto_limpio
    
    def procesar_todas_imagenes(self):
        """
        Procesar todas las imágenes encontradas en S3
        """
        logger.info("🚀 Iniciando procesamiento OCR masivo...")
        
        # Obtener lista de imágenes
        imagenes = self.listar_imagenes_s3()
        if not imagenes:
            logger.error("❌ No hay imágenes para procesar")
            return None
        
        resultados = []
        placas_unicas = set()
        
        # Procesar cada imagen
        for i, imagen_key in enumerate(imagenes, 1):
            logger.info(f"🔍 Procesando {i}/{len(imagenes)}: {imagen_key}")
            
            placas = self.detectar_placa_rekognition(imagen_key)
            
            if placas:
                # Tomar la placa con mayor confianza
                mejor_placa = max(placas, key=lambda x: x['confianza'])
                resultados.append(mejor_placa)
                placas_unicas.add(mejor_placa['placa'])
                
                logger.info(f"✅ Placa detectada: {mejor_placa['placa']} ({mejor_placa['confianza']}%)")
                self.stats['placas_detectadas'] += 1
            else:
                logger.warning(f"⚠️  Sin placas válidas en: {imagen_key}")
            
            self.stats['imagenes_procesadas'] += 1
            
            # Progreso cada 50 imágenes
            if i % 50 == 0:
                logger.info(f"📊 Progreso: {i}/{len(imagenes)} - Placas: {len(placas_unicas)}")
        
        # Estadísticas finales
        self.stats['placas_validas'] = len(placas_unicas)
        self.stats['fin'] = datetime.now()
        self.stats['duracion'] = (self.stats['fin'] - self.stats['inicio']).total_seconds()
        
        return self.generar_resultados(resultados, list(placas_unicas))
    
    def generar_resultados(self, resultados, placas_unicas):
        """
        Generar archivos de resultados
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Archivo completo con detalles
        archivo_completo = self.results_dir / f'placas_detallado_{timestamp}.json'
        with open(archivo_completo, 'w', encoding='utf-8') as f:
            json.dump({
                'estadisticas': self.stats,
                'resultados_detallados': resultados,
                'placas_unicas': placas_unicas
            }, f, indent=2, ensure_ascii=False, default=str)
        
        # 2. Archivo simple para Django seeder
        archivo_seeder = self.results_dir / 'placas_para_seeder.json'
        placas_seeder = []
        for i, placa in enumerate(placas_unicas, 1):
            placas_seeder.append({
                'id': i,
                'placa': placa,
                'activo': True,
                'fecha_registro': datetime.now().isoformat()
            })
        
        with open(archivo_seeder, 'w', encoding='utf-8') as f:
            json.dump(placas_seeder, f, indent=2, ensure_ascii=False, default=str)
        
        # 3. Lista simple TXT
        archivo_txt = self.results_dir / 'lista_placas.txt'
        with open(archivo_txt, 'w', encoding='utf-8') as f:
            for placa in sorted(placas_unicas):
                f.write(f"{placa}\n")
        
        # Log de resultados
        logger.info("🎉 PROCESAMIENTO COMPLETADO!")
        logger.info(f"📊 Estadísticas:")
        logger.info(f"   - Imágenes procesadas: {self.stats['imagenes_procesadas']}")
        logger.info(f"   - Placas detectadas: {self.stats['placas_detectadas']}")
        logger.info(f"   - Placas únicas válidas: {self.stats['placas_validas']}")
        logger.info(f"   - Errores: {self.stats['errores']}")
        logger.info(f"   - Duración: {self.stats['duracion']:.1f} segundos")
        logger.info(f"📁 Archivos generados:")
        logger.info(f"   - Detallado: {archivo_completo}")
        logger.info(f"   - Para seeder: {archivo_seeder}")
        logger.info(f"   - Lista simple: {archivo_txt}")
        
        return archivo_seeder


if __name__ == "__main__":
    try:
        processor = S3OCRProcessor()
        resultado = processor.procesar_todas_imagenes()
        
        if resultado:
            print(f"\n🎉 ¡Éxito! Archivo para seeder Django:")
            print(f"📁 {resultado}")
            print(f"\n📋 Próximos pasos:")
            print(f"1. Revisar archivo generado")
            print(f"2. Integrar con seeder de vehículos de María") 
            print(f"3. Poblar base de datos")
            print(f"4. ¡Probar sistema de detección en vivo!")
        else:
            print("❌ Error en el procesamiento")
            
    except KeyboardInterrupt:
        print("\n⏹️  Procesamiento interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Asegúrate de que:")
        print("- Las credenciales AWS estén configuradas")
        print("- El bucket S3 exista y tenga las imágenes")
        print("- Tengas permisos de S3 y Rekognition")