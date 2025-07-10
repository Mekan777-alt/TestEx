import asyncio
import logging
from typing import Optional
from openai import Client
import aiohttp
from core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Сервис для категоризации жалоб через OpenAI GPT"""

    def __init__(self):
        self.api_key = settings.openai_settings.api_key
        self.model = settings.openai_settings.model
        self.max_tokens = settings.openai_settings.max_tokens
        self.temperature = settings.openai_settings.temperature
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.timeout = 30
        self._session: Optional[aiohttp.ClientSession] = None

    def _create_categorization_prompt(self, text: str) -> str:
        prompt = f"""Определи категорию жалобы клиента. 

Текст жалобы: "{text}"

Возможные категории:
- техническая (проблемы с работой сервиса, техническими функциями, SMS, приложением)
- оплата (вопросы по биллингу, платежам, тарифам, списаниям)
- другое (все остальные вопросы)

Ответь только одним словом из предложенных вариантов."""
        return prompt

    async def send_openai_request(self, text: str):
        """Отправка запроса к OpenAI API"""
        client = Client(api_key=self.api_key)

        completion = client.chat.completions.create(
            model=self.model,
            store=True,
            messages=[
                {"role": "user", "content": self._create_categorization_prompt(text)},
            ]
        )

        return completion.choices[0].message

    async def categorize_complaint(self, text: str) -> str:
        if not text or not text.strip():
            return "другое"

        try:
            response_data = await self.send_openai_request(text)


            content = response_data.content.lower()

            # Валидация категории
            valid_categories = ["техническая", "оплата", "другое"]

            for category in valid_categories:
                if category in content:
                    logger.info(f"AI categorized complaint as: {category}")
                    return category

            if any(word in content for word in ["техническ", "technical", "sms", "приложени"]):
                return "техническая"
            elif any(word in content for word in ["оплат", "payment", "billing", "тариф"]):
                return "оплата"

            logger.warning(f"Could not determine category from AI response: {content}")
            return "другое"

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                logger.error("OpenAI API authentication failed - check API key")
            elif e.status == 429:
                logger.error("OpenAI API rate limit exceeded - try again later")
            elif e.status == 400:
                logger.error("OpenAI API bad request - check prompt format")
            else:
                logger.error(f"OpenAI API error: {e}")
            return "другое"

        except asyncio.TimeoutError:
            logger.error("OpenAI API timeout")
            return "другое"

        except Exception as e:
            logger.error(f"Unexpected error in AI categorization: {e}")
            return "другое"

    async def health_check(self) -> bool:
        try:
            result = await self.categorize_complaint("Тестовое сообщение")
            return result in ["техническая", "оплата", "другое"]
        except Exception:
            return False

    async def close(self):
        """Закрытие HTTP сессии"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def get_ai_service() -> AIService:
    """Dependency для получения AI сервиса"""
    return AIService()