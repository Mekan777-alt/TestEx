from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    def extract_client_ip(self, request: Request) -> Optional[str]:
        headers_to_check = [
            "x-forwarded-for",
            "x-real-ip",
            "cf-connecting-ip",
            "x-client-ip"
        ]

        for header in headers_to_check:
            ip = request.headers.get(header)
            if ip:
                # Берем первый IP из списка (в случае X-Forwarded-For)
                return ip.split(',')[0].strip()

        return request.client.host if request.client else None

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = self.extract_client_ip(request)

        # Добавляем IP в state запроса
        request.state.client_ip = client_ip

        # Логируем для отладки
        if client_ip:
            logger.debug(f"Request from IP: {client_ip} to {request.url.path}")
        else:
            logger.warning(f"Could not determine client IP for {request.url.path}")

        # Продолжаем обработку запроса
        response = await call_next(request)

        return response


class GeolocationMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp, enable_geolocation: bool = True):
        super().__init__(app)
        self.enable_geolocation = enable_geolocation
        self._location_service = None

    @property
    def location_service(self):
        if self._location_service is None:
            from api.services.location_service import LocationService
            self._location_service = LocationService()
        return self._location_service

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            location = await self.location_service.get_location(request.state.client_ip)
            request.state.client_location = location
            logger.info(f"Location detected for {request.state.client_ip}: {location}")
        except Exception as e:
            logger.error(f"Geolocation failed: {e}")
            request.state.client_location = None

        response = await call_next(request)

        return response