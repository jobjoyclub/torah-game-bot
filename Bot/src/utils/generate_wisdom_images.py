#!/usr/bin/env python3
"""
Скрипт для генерации 20 заготовленных изображений для ежедневной мудрости
Используется для оптимизации скорости ответа пользователю
"""

import asyncio
import logging
import os
import sys
import httpx
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from torah_bot.quiz_topics import QuizTopicGenerator
from torah_bot.prompt_loader import PromptLoader

# Load OpenAI from environment
try:
    from openai import AsyncOpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logging.error("❌ OPENAI_API_KEY not found in environment")
        sys.exit(1)
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
     logging.info("✅ OpenAI client initialized")
except ImportError:
     logging.error("❌ OpenAI library not available")
    sys.exit(1)

class WisdomImageGenerator:
    """Генератор заготовленных изображений для мудрости"""
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.output_dir = Path("src/images/wisdom_presets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_preset_images(self, count: int = 20):
        """Генерирует заготовленные изображения для ежедневной мудрости"""
         logging.info(f"🎨 Generating {count} preset wisdom images...")
        
        # Выбираем 20 самых разнообразных тем
        topics = QuizTopicGenerator.get_multiple_topics(count)
        
        generated_images = []
        
        for i, topic in enumerate(topics, 1):
             logging.info(f"📸 Image {i}/{count}: {topic}")
            
            try:
                # Получаем тематические элементы
                theme_elements = self.prompt_loader.get_theme_elements(topic)
                
                # Создаем промпт для изображения
                image_prompt = self.prompt_loader.get_wisdom_image_prompt(topic, theme_elements)
                
                 logging.info(f"   🎯 Theme: {theme_elements[:50]}...")
                
                # Генерируем изображение
                response = await openai_client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    size="1024x1024",
                    quality="hd",  # Высокое качество для заготовок
                    n=1
                )
                
                if response.data and len(response.data) > 0:
                    image_url = response.data[0].url
                    
                    # Скачиваем изображение
                    filename = f"wisdom_{i:02d}_{topic.replace(' ', '_').replace('/', '_')[:30]}.jpg"
                    filepath = self.output_dir / filename
                    
                    async with httpx.AsyncClient() as client:
                        if image_url:
                            img_response = await client.get(image_url)
                            if img_response.status_code == 200:
                                filepath.write_bytes(img_response.content)
                             logging.info(f"   ✅ Saved: {filename}")
                            generated_images.append({
                                "filename": filename,
                                "topic": topic,
                                "theme_elements": theme_elements
                            })
                        else:
                             logging.warning(f"   ❌ Failed to download image for {topic}")
                else:
                     logging.warning(f"   ❌ No image generated for {topic}")
                    
            except Exception as e:
                 logging.error(f"   ❌ Error generating image for {topic}: {e}")
                
            # Небольшая пауза между запросами
            await asyncio.sleep(1)
        
         logging.info(f"🎉 Generated {len(generated_images)} preset images!")
        
        # Создаем метаданные файл
        metadata_content = "# Preset Wisdom Images Metadata\n\n"
        for img in generated_images:
            metadata_content += f"## {img['filename']}\n"
            metadata_content += f"- **Topic:** {img['topic']}\n"
            metadata_content += f"- **Theme:** {img['theme_elements']}\n\n"
            
        metadata_file = self.output_dir / "metadata.md"
        metadata_file.write_text(metadata_content, encoding='utf-8')
         logging.info(f"📋 Metadata saved to {metadata_file}")
        
        return generated_images

async def main():
    """Основная функция генерации"""
    generator = WisdomImageGenerator()
    await generator.generate_preset_images(20)

if __name__ == "__main__":
    asyncio.run(main())