"""Корневой роутер API."""

from fastapi import APIRouter

from may_walk.api.routers.authentication import router as authentication_router
from may_walk.api.routers.health import router as health_router
from may_walk.api.routers.route.crud import router as route_crud_router
from may_walk.api.routers.route.exports import router as route_exports_router
from may_walk.api.routers.route.imports import router as route_imports_router
from may_walk.api.routers.route.stats import router as route_stats_router

api_router = APIRouter()
api_router.include_router(authentication_router)
api_router.include_router(health_router)
api_router.include_router(route_imports_router)
api_router.include_router(route_exports_router)
api_router.include_router(route_stats_router)
api_router.include_router(route_crud_router)
