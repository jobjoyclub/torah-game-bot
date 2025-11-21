"""
Utility для загрузки промптов из файлов
"""
import os
import random
from typing import Dict, List

class PromptLoader:
    def __init__(self, prompts_dir: str = ""):
        if not prompts_dir:
            # Путь относительно текущего файла
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompts_dir = os.path.join(current_dir, "prompts")
        self.prompts_dir = prompts_dir
        self._cache = {}
    
    def load_prompt(self, filename: str) -> str:
        """Загружает промпт из файла с кешированием"""
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = os.path.join(self.prompts_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self._cache[filename] = content
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
    
    def get_rabbi_wisdom_prompt(self, user_name: str, language: str, user_text: str, 
                                 add_variety: bool = True) -> str:
        """Возвращает промпт для генерации wisdom с опциональным разнообразием"""
        template = self.load_prompt("rabbi_wisdom.txt")
        
        # Add variety instruction for more diverse content (like quiz does)
        variety_instruction = ""
        if add_variety:
            try:
                variety_elements = self.load_wisdom_variety_elements()
                variety_instruction = random.choice(variety_elements)
                # Prepend variety to user_text
                user_text_with_variety = f"{user_text}\n\nStyle guidance: {variety_instruction}"
                return template.format(user_name=user_name, language=language, user_text=user_text_with_variety)
            except Exception as e:
                # If variety loading fails, continue without it
                pass
        
        return template.format(user_name=user_name, language=language, user_text=user_text)
    
    def get_user_wisdom_prompt(self, user_text: str) -> str:
        """Возвращает user промпт для wisdom"""
        template = self.load_prompt("user_prompt_wisdom.txt")
        return template.format(user_text=user_text)
    
    def get_quiz_prompt(self, topic: str, language: str, duplicate_warning: str = "") -> str:
        """Возвращает промпт для генерации quiz с случайным элементом разнообразия"""
        try:
            template = self.load_prompt("torah_quiz.txt")
            variety_elements = self.load_quiz_variety_elements()
            variety_instruction = random.choice(variety_elements)
            
            return template.format(
                topic=topic,
                language=language,
                variety_instruction=variety_instruction,
                duplicate_warning=duplicate_warning
            )
        except Exception as e:
            # Log error and return fallback template
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"PROMPT LOADER EXCEPTION: {e}")
            logger.error(f"TRACEBACK: {traceback.format_exc()}")
            
            # Return minimal working prompt as fallback
            return f"""Create a Torah/Talmud quiz question on the topic: {topic}
Write the quiz in {language}
Create EXACTLY 6 answer options
Return ONLY valid JSON format:
{{"question": "Your question", "options": ["A", "B", "C", "D", "E", "F"], "correct_answer": 0, "explanation": "Explanation", "follow_up": "Question"}}"""
    
    def load_quiz_variety_elements(self) -> List[str]:
        """Загружает элементы разнообразия для quiz"""
        content = self.load_prompt("quiz_variety_elements.txt")
        return [line.strip() for line in content.split('\n') if line.strip()]
    
    def load_wisdom_variety_elements(self) -> List[str]:
        """Загружает элементы разнообразия для wisdom (NEW: October 2025)"""
        content = self.load_prompt("wisdom_variety_elements.txt")
        return [line.strip() for line in content.split('\n') if line.strip()]
    
    def get_wisdom_image_prompt(self, topic: str, theme_elements: str = "") -> str:
        """Возвращает промпт для генерации изображения мудрости с адаптивными элементами"""
        try:
            template = self.load_prompt("wisdom_image.txt")
            return template.format(
                topic=topic,
                theme_specific_elements=theme_elements
            )
        except Exception as e:
            # Fallback промпт если файл недоступен
            return f"Peaceful library study scene about {topic}. Warm lighting, books and scrolls on wooden shelves, cozy reading atmosphere, no text visible."
    
    def get_theme_elements(self, topic: str) -> str:
        """Возвращает тематические элементы для разных видов мудрости"""
        theme_mapping = {
            # English themes
            "family": "Family gathering around Shabbat table, multi-generational warmth",
            "work": "Ancient craftsman's tools, scrolls with wisdom, peaceful study",  
            "study": "Open books, scrolls, candlelit study room, focused learning",
            "prayer": "Tallit and tefillin, morning light through synagogue windows",
            "shabbat": "Shabbat candles, challah, peaceful family scene",
            "love": "Two figures walking peaceful garden, wedding elements, romantic harmony",
            "wisdom": "Ancient sage with scroll, tree of knowledge, contemplative scene",
            "peace": "Dove with olive branch, harmonious landscape, calm waters",
            "charity": "Hands helping others, community support, acts of kindness, warm atmosphere",
            "marriage": "Wedding ceremony, chuppah, couple under stars, celebration",
            "children": "Children learning Torah, family reading together, joy and laughter",
            "sex": "Intimate couple connection, sacred marriage bond, private bedroom scene, warm candlelight",
            "sexuality": "Romantic couple harmony, sacred intimacy, bedroom with soft lighting",
            "intimacy": "Close couple connection, private romantic setting, soft warm atmosphere",
            "intimate": "Romantic intimate scene, couple in private setting, soft candlelight",
            
            # Russian themes
            "любовь": "Two figures walking peaceful garden, wedding elements, romantic harmony, heart symbols",
            "добрые дела": "Hands helping others, community support, acts of kindness, warm atmosphere",
            "мудрость": "Wise teacher with books, ancient scrolls, study atmosphere, contemplative scene",
            "семья": "Family gathering around table, multi-generational warmth, peaceful home",
            "молитва": "Peaceful meditation space, morning light through windows, contemplative atmosphere",
            "отношения": "People connecting, friendship, community bonds, warm interactions",
            "учёба": "Open books, scrolls, candlelit study room, focused learning atmosphere",
            "тора": "Torah scrolls, ancient texts, study scene, traditional learning",
            "праздник": "Celebration, Jewish holidays, candles, festive atmosphere",
            "дом": "Peaceful home, family warmth, mezuzah, domestic harmony",
            "брак": "Wedding ceremony, chuppah, couple under stars, celebration of love",
            "дети": "Children learning Torah, family reading together, joy and laughter",
            "секс": "Intimate couple connection, sacred marriage bond, private bedroom scene, warm candlelight",
            "сексуальность": "Romantic couple harmony, sacred intimacy, bedroom with soft lighting",
            "интимность": "Close couple connection, private romantic setting, soft warm atmosphere",
            "интимные отношения": "Romantic intimate scene, couple in private setting, soft candlelight",
            "обсуждение секса": "Intimate couple connection, sacred marriage bond, private bedroom scene, warm candlelight",
            "обсуждение": "Intimate couple connection, sacred marriage bond, private bedroom scene, warm candlelight"
        }
        
        topic_lower = topic.lower()
        for keyword, elements in theme_mapping.items():
            if keyword in topic_lower:
                # Theme match found
                return elements
        
        # Using default theme
        return "Traditional Jewish symbols, peaceful contemplative scene"
    
    def reload_cache(self):
        """Очищает кеш для перезагрузки промптов"""
        self._cache.clear()