import logging
from typing import Optional
from core.config import settings
import aiohttp

logger = logging.Logger(__name__)


class SpamService:
    def __init__(self):
        self.url = settings.optional_api_settings.spam_api_url
        self.api_key = settings.optional_api_settings.spam_api_key
        self.timeout = 5
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Получение HTTP сессии"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session


    async def check_spam(self, text: str) -> bool:
        if not self.api_key:
            logger.warning("Spam API key not configured")
            return False

        try:
            session = await self.get_session()

            headers = {
                "apikey": self.api_key
            }

            payload = {
                "text": text.strip()
            }

            async with session.post(self.url, headers=headers, json=payload, ssl=False) as response:
                response_text = await response.text()

                if response.status == 200:
                    try:
                        data = await response.json() if response_text else {}
                        logger.info(f"Успех Spam API: {data}")
                        return data.get("is_spam")
                    except Exception as e:
                        logger.error(f"Не удалось проанализировать ответ JSON: {e}")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message="Неверный ответ JSON"
                        )
        except Exception as e:
            logger.error(f"Error in spam check: {e}")
            return False

    async def close(self):
        """Закрытие HTTP сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


def get_spam_service() -> SpamService:
    return SpamService()