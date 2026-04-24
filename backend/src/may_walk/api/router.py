"""Корневой роутер API."""

from fastapi import APIRouter

from may_walk.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
