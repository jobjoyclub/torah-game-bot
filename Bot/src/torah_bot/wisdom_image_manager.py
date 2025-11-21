"""
Менеджер изображений для мудрости раввина
Обеспечивает быстрый ответ через заготовленные изображения
"""

import random
import os
from pathlib import Path
from typing import Optional, List

class WisdomImageManager:
    """Управляет заготовленными изображениями для ежедневной мудрости"""
    
    def __init__(self):
        self.preset_dir = Path(__file__).parent.parent / "images" / "wisdom_presets"
        self._preset_images = self._load_preset_images()
        
    def _load_preset_images(self) -> List[str]:
        """Загружает список заготовленных изображений"""
        if not self.preset_dir.exists():
            return []
            
        # Ищем все .jpg файлы с префиксом wisdom_
        preset_files = []
        for file in self.preset_dir.glob("wisdom_*.jpg"):
            preset_files.append(file.name)
            
        return sorted(preset_files)  # Сортируем для предсказуемости
        
    def get_random_preset_image(self, exclude_recent: Optional[List[str]] = None) -> Optional[str]:
        """
        Возвращает путь к случайному заготовленному изображению
        
        Args:
            exclude_recent: Список недавно использованных изображений для избегания повторов
            
        Returns:
            Полный путь к файлу изображения или None если нет доступных изображений
        """
        if not self._preset_images:
            return None
            
        # Фильтруем недавно использованные
        available_images = self._preset_images
        if exclude_recent:
            available_images = [img for img in self._preset_images if img not in exclude_recent]
            
        # Если отфильтровали все, используем полный список
        if not available_images:
            available_images = self._preset_images
            
        # Выбираем случайное изображение
        selected_image = random.choice(available_images)
        
        # Возвращаем полный путь
        return str(self.preset_dir / selected_image)
        
    def get_preset_count(self) -> int:
        """Возвращает количество доступных заготовленных изображений"""
        return len(self._preset_images)
        
    def has_presets(self) -> bool:
        """Проверяет, есть ли заготовленные изображения"""
        return len(self._preset_images) > 0
        
    def get_preset_info(self) -> dict:
        """Возвращает информацию о заготовленных изображениях"""
        return {
            "count": self.get_preset_count(),
            "available": self.has_presets(),
            "images": self._preset_images[:5],  # Первые 5 для демонстрации
            "preset_dir": str(self.preset_dir)
        }