from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


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