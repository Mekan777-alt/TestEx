import asyncio
import logging
from typing import Optional, Dict, Any
from core.config import settings
import aiohttp

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self):
        self.url = settings.optional_api_settings.ip_api_url
        self.timeout = 10
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def send_request(self, ip: str) -> Dict[str, Any]:
        if not ip or not ip.strip():
            raise ValueError("IP address cannot be empty")

        session = await self.get_session()

        url = f"{self.url}/{ip.strip()}"

        logger.debug(f"Requesting geolocation for IP: {ip}")

        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.debug(f"Geolocation API response: {data}")
                return data
            else:
                error_text = await response.text()
                logger.error(f"Geolocation API error {response.status}: {error_text}")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )

    async def get_location(self, ip: str) -> Optional[str]:
        try:
            response_data = await self.send_request(ip)

            # Проверяем успешность запроса
            status = response_data.get("status")
            if status != "success":
                logger.warning(f"Geolocation failed for {ip}: {response_data.get('message', 'Unknown error')}")
                return None

            # Формируем строку с локацией
            city = response_data.get("city", "")
            region = response_data.get("regionName", "")
            country = response_data.get("country", "")

            # Составляем адрес
            location_parts = []
            if city:
                location_parts.append(city)
            if region and region != city:
                location_parts.append(region)
            if country:
                location_parts.append(country)

            if location_parts:
                location = ", ".join(location_parts)
                logger.info(f"Location for {ip}: {location}")
                return location
            else:
                logger.warning(f"Нет данных о местоположении для {ip}")
                return None

        except ValueError as e:
            logger.error(f"Ошибка валидации: {e}")
            return None

        except asyncio.TimeoutError:
            logger.error(f"Тайм-аут геолокации для {ip}")
            return None

        except aiohttp.ClientError as e:
            logger.error(f"Ошибка HTTP в геолокации: {e}")
            return None

        except Exception as e:
            logger.error(f"Неожиданная ошибка геолокации: {e}")
            return None

    async def get_detailed_location(self, ip: str) -> Optional[Dict[str, Any]]:
        try:
            response_data = await self.send_request(ip)

            if response_data.get("status") == "success":
                return {
                    "ip": response_data.get("query"),
                    "country": response_data.get("country"),
                    "country_code": response_data.get("countryCode"),
                    "region": response_data.get("regionName"),
                    "region_code": response_data.get("region"),
                    "city": response_data.get("city"),
                    "zip": response_data.get("zip"),
                    "lat": response_data.get("lat"),
                    "lon": response_data.get("lon"),
                    "timezone": response_data.get("timezone"),
                    "isp": response_data.get("isp"),
                    "organization": response_data.get("org")
                }
            return None

        except Exception as e:
            logger.error(f"Error getting detailed location: {e}")
            return None

    async def close(self):
        """Закрытие HTTP сессии"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def get_location_service() -> LocationService:
    return LocationService()
