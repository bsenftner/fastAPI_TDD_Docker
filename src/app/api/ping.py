from fastapi import APIRouter

from app import config


router = APIRouter()


@router.get("/ping")
async def pong():
    return {"ping": "pong!",
            "environment": config.settings.ENVIRONMENT,
            "testing": config.settings.TESTING,
           }
