from fastapi import APIRouter

from app import config


router = APIRouter()


@router.get("/ping")
async def pong():
    return {
        "ping": "pong!",
        "environment": config.get_settings().ENVIRONMENT,
        "testing": config.get_settings().TESTING,
           }
