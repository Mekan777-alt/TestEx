import asyncio
import logging
from typing import Optional, Dict, Any

import aiohttp
from core.config import settings

logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self):
        self.url = settings.sentiment_api_settings.base_url
        self.api_key = settings.sentiment_api_settings.api_key
        self.timeout = settings.sentiment_api_settings.timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def send_request(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("Текст не может быть пустым")

        session = await self.get_session()

        headers = {
            "apikey": self.api_key,
        }

        payload = {
            "text": text.strip()
        }

        logger.debug(f"Отправка запроса на анализ настроений по длине текста: {len(text)}")

        async with session.post(self.url, headers=headers, json=payload, ssl=False) as response:
            response_text = await response.text()

            if response.status == 200:
                try:
                    data = await response.json() if response_text else {}
                    logger.info(f"Успех Sentiment API: {data}")
                    return data
                except Exception as e:
                    logger.error(f"Не удалось проанализировать ответ JSON: {e}")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message="Неверный ответ JSON"
                    )

            error_message = response_text
            try:
                error_data = await response.json() if response_text else {}
                error_message = error_data.get('message', response_text)
            except:
                pass

            # Обработка конкретных кодов ошибок APILayer
            if response.status == 400:
                logger.error(f"Sentiment API - Bad Request (400): {error_message}")
                logger.error("Возможные причины: отсутствует обязательный параметр, неверный формат текста.")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Bad Request: {error_message}"
                )

            elif response.status == 401:
                logger.error(f"Sentiment API - Unauthorized (401): {error_message}")
                logger.error("Ключ API недействителен или отсутствует")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Unauthorized: действительный ключ API не предоставлен. {error_message}"
                )

            elif response.status == 404:
                logger.error(f"Sentiment API - Not Found (404): {error_message}")
                logger.error("Запрошенный ресурс не существует — проверьте конечную точку API")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Resource not found: {error_message}"
                )

            elif response.status == 429:
                logger.error(f"Sentiment API - Rate Limit (429): {error_message}")
                logger.error("Превышен лимит запросов API")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Rate limit exceeded: {error_message}"
                )

            elif 500 <= response.status < 600:
                logger.error(f"Sentiment API - Server Error ({response.status}): {error_message}")
                logger.error("Сервер APILayer не смог обработать запрос")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Server error: {error_message}"
                )

            else:
                logger.error(f"Sentiment API - Unexpected error ({response.status}): {error_message}")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Unexpected error: {error_message}"
                )

    async def analyze_sentiment(self, text: str) -> str:
        try:
            response_data = await self.send_request(text)

            # Парсинг ответа APILayer
            sentiment = response_data.get("sentiment", "unknown").lower()
            confidence = response_data.get("confidence", 0)

            # Валидация результата
            valid_sentiments = ["positive", "negative", "neutral"]
            if sentiment in valid_sentiments:
                logger.info(f"Sentiment detected: {sentiment} (confidence: {confidence})")
                return sentiment
            else:
                logger.warning(f"Invalid sentiment value: {sentiment}")
                return "unknown"

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return "unknown"

        except asyncio.TimeoutError:
            logger.error("Sentiment analysis timeout")
            return "unknown"

        except aiohttp.ClientResponseError as e:
            if e.status == 400:
                logger.error("Неправильный запрос к Sentiment API — проверьте формат текста")
            elif e.status == 401:
                logger.error("Ошибка аутентификации Sentiment API — проверьте ключ API в настройках")
            elif e.status == 404:
                logger.error("Конечная точка Sentiment API не найдена — проверьте конфигурацию URL")
            elif e.status == 429:
                logger.error("Превышен лимит Sentiment API — повторите попытку позже")
            elif 500 <= e.status < 600:
                logger.error("Ошибка сервера Sentiment API — сервис временно недоступен")

            return "unknown"

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in sentiment analysis: {e}")
            return "unknown"

        except Exception as e:
            logger.error(f"Unexpected error in sentiment analysis: {e}")
            return "unknown"

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def health_check(self) -> bool:
        """Проверка работоспособности сервиса"""
        try:
            result = await self.analyze_sentiment("This is a test message")
            return result != "unknown"
        except Exception:
            return False


def get_sentiment_service() -> SentimentService:
    return SentimentService()
