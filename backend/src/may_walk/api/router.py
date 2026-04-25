"""Корневой роутер API."""

from fastapi import APIRouter

from may_walk.api.routers.auth import router as auth_router
from may_walk.api.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
