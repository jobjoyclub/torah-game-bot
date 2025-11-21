"""
Разнообразные темы для автоматической генерации Torah Quiz
"""
import random
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QuizTopicGenerator:
    """Генератор разнообразных тем для квизов"""
    
    # EXPANDED: 75+ diverse quiz topics for unique content (October 2025)
    DIVERSE_TOPICS = [
        # Biblical figures and stories (20 topics)
        "Abraham and the binding of Isaac",
        "Moses and the burning bush", 
        "King David and his psalms",
        "Queen Esther and Purim miracle",
        "Joseph and his prophetic dreams",
        "Noah and the rainbow covenant",
        "Sarah and the promise of descendants",
        "Jacob's ladder and divine vision",
        "Ruth's loyalty and conversion",
        "Solomon's wisdom and the Temple",
        "Daniel in the lion's den",
        "Jonah and repentance lessons",
        "Rebecca at the well",
        "Rachel and Leah's sisterhood",
        "Aaron the High Priest",
        "Miriam the prophetess",
        "Joshua and the walls of Jericho",
        "Deborah the judge and leader",
        "Samuel the prophet",
        "Elijah and Mount Carmel miracle",
        
        # Jewish holidays and observances (15 topics)
        "Passover traditions and freedom",
        "Yom Kippur forgiveness and atonement", 
        "Sukkot divine protection and joy",
        "Hanukkah miracle of light",
        "Shabbat peace and sanctity",
        "Rosh Hashanah new year and judgement",
        "Purim joy and hidden miracles",
        "Shavuot and receiving the Torah",
        "Tu B'Shvat and environmental care",
        "Tisha B'Av mourning and hope",
        "Lag BaOmer celebrations",
        "Simchat Torah dancing with scrolls",
        "Fast of Esther spiritual preparation",
        "Chanukah gelt tradition meaning",
        "Counting of the Omer spiritual journey",
        
        # Ethics and wisdom (15 topics)
        "Jewish concept of charity tzedakah",
        "Talmudic wisdom about relationships",
        "Rabbi Hillel's golden rule",
        "Jewish views on justice and mercy",
        "Importance of Torah study",
        "Jewish teachings about kindness",
        "Concept of tikkun olam world repair",
        "Lashon hara avoiding gossip",
        "Honoring parents and elders",
        "Business ethics in Jewish law",
        "Environmental stewardship in Torah",
        "Peace and conflict resolution",
        "Gratitude and blessings daily",
        "Truthfulness and integrity",
        "Humility in Jewish thought",
        
        # Kabbalah and mysticism (10 topics)
        "Tree of Life and spiritual growth",
        "Jewish mystical sefirot concepts", 
        "Holy Names of God",
        "Jewish meditation kavanah practices",
        "Zohar wisdom and teachings",
        "Gematria numerical meanings",
        "Four spiritual worlds",
        "Souls and reincarnation gilgul",
        "Mystical meaning of Hebrew letters",
        "Shabbat bride mystical concept",
        
        # Daily life and practice (15 topics)
        "Kosher laws dietary significance",
        "Jewish wedding traditions chuppah",
        "Bar Bat Mitzvah coming of age",
        "Jewish prayer practices tefillah",
        "Mezuzah and home blessings",
        "Tefillin phylacteries meaning",
        "Tallit prayer shawl symbolism",
        "Mikvah ritual immersion",
        "Shofar ram's horn significance",
        "Havdalah ceremony ending Shabbat",
        "Blessings bracha for daily activities",
        "Jewish naming ceremonies",
        "Pidyon HaBen firstborn redemption",
        "Challah bread Shabbat symbolism",
        "Candle lighting women's mitzvah"
    ]
    
    @classmethod
    def get_random_topic(cls, exclude_recent: Optional[List[str]] = None) -> str:
        """Возвращает случайную тему, избегая недавно использованных"""
        if exclude_recent:
            available_topics = [t for t in cls.DIVERSE_TOPICS if t not in exclude_recent]
            if not available_topics:
                logger.warning(f"🔄 All {len(cls.DIVERSE_TOPICS)} topics were used recently - resetting exclusion list")
                available_topics = cls.DIVERSE_TOPICS
        else:
            available_topics = cls.DIVERSE_TOPICS
            
        selected_topic = random.choice(available_topics)
        if exclude_recent:
            logger.info(f"🎯 Selected unique topic: '{selected_topic}' (excluded {len(exclude_recent)} recent topics)")
        else:
            logger.info(f"🎯 Selected random topic: '{selected_topic}' (no exclusions)")
        return selected_topic
    
    @classmethod
    def get_multiple_topics(cls, count: int = 5) -> List[str]:
        """Возвращает несколько разных тем"""
        return random.sample(cls.DIVERSE_TOPICS, min(count, len(cls.DIVERSE_TOPICS)))
    
    @classmethod
    async def get_unique_topic(cls, db_pool, days_back: int = 21) -> str:
        """Возвращает тему, не использованную последние N дней (INCREASED: 7->21 for better variety)"""
        try:
            if not db_pool:
                logger.warning("🔄 DB pool not available - using random topic selection")
                return cls.get_random_topic()
                
            # Get recent quiz topics from database
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            async with db_pool.acquire() as conn:
                # This query was redundant - removing it since we have the corrected one below
                
                # Filter only quiz broadcast types for accurate exclusion (FIXED SCHEMA)
                recent_quiz_topics = await conn.fetch("""
                    SELECT DISTINCT wisdom_content->>'topic' as quiz_topic 
                    FROM newsletter_broadcasts 
                    WHERE wisdom_content->>'type' = 'quiz'
                    AND created_at >= $1
                    ORDER BY wisdom_content->>'topic'
                """, cutoff_date)
                
                exclude_list = [row['quiz_topic'] for row in recent_quiz_topics if row['quiz_topic']]
                logger.info(f"📊 Found {len(exclude_list)} QUIZ topics used in last {days_back} days")
                
                return cls.get_random_topic(exclude_recent=exclude_list)
                
        except Exception as e:
            logger.error(f"❌ Failed to get unique topic from DB: {e} - using random selection")
            return cls.get_random_topic()
    
    @classmethod
    async def save_quiz_topic(cls, db_pool, topic: str, broadcast_date: date) -> bool:
        """Сохраняет тему квиза в базу данных для отслеживания (с UPSERT)"""
        try:
            if not db_pool:
                logger.warning("🔄 DB pool not available - cannot save quiz topic")
                return False
                
            async with db_pool.acquire() as conn:
                # UPSERT quiz topic with CORRECT SCHEMA (using wisdom_content JSONB)
                import json
                quiz_content = json.dumps({
                    "type": "quiz",
                    "topic": topic,
                    "created_by": "auto_quiz_system",
                    "timestamp": broadcast_date.isoformat()
                })
                
                # FIX: Add broadcast_type to prevent conflicts with wisdom broadcasts
                await conn.execute("""
                    INSERT INTO newsletter_broadcasts 
                    (broadcast_date, broadcast_type, wisdom_content, status, created_by)
                    VALUES ($1, 'quiz', $2, 'ready', 'auto_quiz_system')
                    ON CONFLICT (broadcast_date, broadcast_type) 
                    DO UPDATE SET wisdom_content = EXCLUDED.wisdom_content, 
                                  status = 'ready',
                                  created_by = 'auto_quiz_system'
                """, broadcast_date, quiz_content)
                
                logger.info(f"✅ UPSERTED quiz topic '{topic}' for {broadcast_date}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to save quiz topic: {e}")
            return False