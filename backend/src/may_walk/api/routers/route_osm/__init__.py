"""Роутеры OSM-операций маршрутов."""

from fastapi import APIRouter

from may_walk.api.routers.route_osm.merge import router as merge_router
from may_walk.api.routers.route_osm.snap import router as snap_router
from may_walk.api.routers.route_osm.stats import router as stats_router

router = APIRouter()
router.include_router(stats_router)
router.include_router(snap_router)
router.include_router(merge_router)

__all__ = ['router']
