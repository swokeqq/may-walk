"""Корневой роутер API."""

from fastapi import APIRouter

from may_walk.api.routers.authentication import router as authentication_router
from may_walk.api.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(authentication_router)
api_router.include_router(health_router)
