"""Корневой роутер API."""

from fastapi import APIRouter

from may_walk.api.routers.authentication import router as authentication_router
from may_walk.api.routers.health import router as health_router
from may_walk.api.routers.route.crud import router as route_crud_router
from may_walk.api.routers.route_file import router as route_file_router
from may_walk.api.routers.route_osm import router as route_osm_router

api_router = APIRouter()
api_router.include_router(authentication_router)
api_router.include_router(health_router)
api_router.include_router(route_file_router)
api_router.include_router(route_osm_router)
api_router.include_router(route_crud_router)
