import logging
from datetime import datetime

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from core.config import settings
from middleware.geo_middleware import GeolocationMiddleware, IPMiddleware
from api.controllers.complaints_controller import router as complaints_router
from database.session import engine
from models.complaint_model import Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_settings.app_name,
    description="API для обработки жалоб клиентов с интеграцией внешних сервисов",
    version="1.0.0",
    debug=settings.app_settings.debug,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware (порядок важен!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем наши middleware
app.add_middleware(GeolocationMiddleware, enable_geolocation=True)
app.add_middleware(IPMiddleware)

# Подключение роутеров
app.include_router(complaints_router)


@app.on_event("startup")
async def startup_event():
    try:
        # Создание таблиц в базе данных
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")
        logger.info(f"Application started successfully on {settings.app_settings.host}:{settings.app_settings.port}")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка ресурсов при остановке приложения"""
    try:
        await engine.dispose()
        logger.info("Application shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Complaints Processing API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Детальная проверка здоровья системы и внешних сервисов
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Проверка базы данных
    try:
        from database.session import get_session
        async for session in get_session():
            await session.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Проверка Sentiment API
    try:
        from api.services.sentiment_service import SentimentService
        sentiment_service = SentimentService()
        if await sentiment_service.health_check():
            health_status["services"]["sentiment_api"] = "healthy"
        else:
            health_status["services"]["sentiment_api"] = "unhealthy"
            health_status["status"] = "degraded"
        await sentiment_service.close()
    except Exception as e:
        health_status["services"]["sentiment_api"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Проверка OpenAI API
    try:
        from api.services.ai_service import AIService, get_ai_service
        ai_service = get_ai_service()
        if await ai_service.health_check():
            health_status["services"]["openai_api"] = "healthy"
        else:
            health_status["services"]["openai_api"] = "unhealthy"
            health_status["status"] = "degraded"
        await ai_service.close()
    except Exception as e:
        health_status["services"]["openai_api"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Проверка геолокации
    try:
        from api.services.location_service import LocationService
        location_service = LocationService()
        test_location = await location_service.get_location("8.8.8.8")  # Google DNS
        if test_location:
            health_status["services"]["geolocation_api"] = "healthy"
        else:
            health_status["services"]["geolocation_api"] = "degraded"
        await location_service.close()
    except Exception as e:
        health_status["services"]["geolocation_api"] = f"degraded: {str(e)}"

    return health_status

