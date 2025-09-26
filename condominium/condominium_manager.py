import json
import os
from django.conf import settings
from typing import Dict, Any, Optional


class CondominiumDataManager:
    """Clase para manejar los datos del condominio desde JSON"""
    
    def __init__(self):
        self.json_file_path = os.path.join(settings.BASE_DIR, 'condominium', 'condominium_data.json')
        self._data = None

    def _load_data(self) -> Dict[str, Any]:
        """Carga los datos del archivo JSON"""
        if self._data is None:
            try:
                with open(self.json_file_path, 'r', encoding='utf-8') as file:
                    self._data = json.load(file)
            except FileNotFoundError:
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.json_file_path}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Error al decodificar JSON: {str(e)}")
        return self._data

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Guarda los datos en el archivo JSON"""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            self._data = data  # Actualizar cache
        except Exception as e:
            raise ValueError(f"Error al guardar datos: {str(e)}")

    def get_all_data(self) -> Dict[str, Any]:
        """Obtiene todos los datos del condominio"""
        return self._load_data()

    def get_condominium_info(self) -> Dict[str, Any]:
        """Obtiene información básica del condominio"""
        data = self._load_data()
        return data.get('condominium_info', {})

    def get_contact_info(self) -> Dict[str, Any]:
        """Obtiene información de contactos"""
        data = self._load_data()
        return data.get('contact_info', {})

    def get_settings(self) -> Dict[str, Any]:
        """Obtiene configuraciones del condominio"""
        data = self._load_data()
        return data.get('settings', {})

    def get_building_info(self) -> Dict[str, Any]:
        """Obtiene información del edificio"""
        data = self._load_data()
        return data.get('building_info', {})

    def get_financial_info(self) -> Dict[str, Any]:
        """Obtiene información financiera"""
        data = self._load_data()
        return data.get('financial_info', {})

    def get_rules_and_regulations(self) -> Dict[str, Any]:
        """Obtiene reglas y regulaciones"""
        data = self._load_data()
        return data.get('rules_and_regulations', {})

    def get_common_areas(self) -> list:
        """Obtiene lista de áreas comunes"""
        settings_data = self.get_settings()
        return settings_data.get('common_areas', [])

    def get_emergency_contacts(self) -> list:
        """Obtiene contactos de emergencia"""
        settings_data = self.get_settings()
        return settings_data.get('emergency_contacts', [])

    def update_condominium_info(self, new_info: Dict[str, Any]) -> None:
        """Actualiza información básica del condominio"""
        data = self._load_data()
        data['condominium_info'].update(new_info)
        self._save_data(data)

    def update_contact_info(self, contact_type: str, new_contact: Dict[str, Any]) -> None:
        """Actualiza información de un contacto específico"""
        data = self._load_data()
        if 'contact_info' not in data:
            data['contact_info'] = {}
        data['contact_info'][contact_type] = new_contact
        self._save_data(data)

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones del condominio"""
        data = self._load_data()
        data['settings'].update(new_settings)
        self._save_data(data)

    def add_common_area(self, common_area: Dict[str, Any]) -> None:
        """Agrega un área común"""
        data = self._load_data()
        if 'settings' not in data:
            data['settings'] = {}
        if 'common_areas' not in data['settings']:
            data['settings']['common_areas'] = []
        data['settings']['common_areas'].append(common_area)
        self._save_data(data)

    def remove_common_area(self, area_name: str) -> bool:
        """Elimina un área común por nombre"""
        data = self._load_data()
        common_areas = data.get('settings', {}).get('common_areas', [])
        
        for i, area in enumerate(common_areas):
            if area.get('name') == area_name:
                del common_areas[i]
                self._save_data(data)
                return True
        return False

    def update_financial_info(self, new_financial: Dict[str, Any]) -> None:
        """Actualiza información financiera"""
        data = self._load_data()
        data['financial_info'].update(new_financial)
        self._save_data(data)

    def get_monthly_maintenance_fee(self) -> float:
        """Obtiene la cuota mensual de mantenimiento"""
        financial_info = self.get_financial_info()
        return financial_info.get('monthly_maintenance_fee', 0.0)

    def get_visitor_hours(self) -> Dict[str, str]:
        """Obtiene horarios de visita"""
        settings_data = self.get_settings()
        return settings_data.get('visitor_hours', {'start': '06:00', 'end': '22:00'})

    def reload_data(self) -> None:
        """Recarga los datos del archivo JSON"""
        self._data = None
        self._load_data()


# Instancia global para usar en toda la aplicación
condominium_data = CondominiumDataManager()