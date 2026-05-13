"""Роутеры файловых операций маршрутов."""

from fastapi import APIRouter

from may_walk.api.routers.route_file.exports import router as exports_router
from may_walk.api.routers.route_file.imports import router as imports_router

router = APIRouter()
router.include_router(imports_router)
router.include_router(exports_router)

__all__ = ['router']
