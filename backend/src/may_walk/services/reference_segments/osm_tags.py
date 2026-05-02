"""Наборы OSM-тегов для классификации опорной сети."""

ASPHALT_SURFACES = frozenset(
    {
        'asphalt',
        'chipseal',
        'concrete',
        'concrete:lanes',
        'concrete:plates',
        'metal',
        'paved',
        'paving_stones',
        'sett',
        'wood',
    }
)
FIELD_PATH_SURFACES = frozenset(
    {
        'clay',
        'compacted',
        'dirt',
        'earth',
        'fine_gravel',
        'grass',
        'grass_paver',
        'gravel',
        'ground',
        'mud',
        'pebblestone',
        'sand',
        'unpaved',
    }
)
FOREST_PATH_SURFACES = frozenset(
    {
        'bark',
        'ground',
        'woodchips',
    }
)
TRACK_HIGHWAYS = frozenset({'track'})
FOREST_PATH_HIGHWAYS = frozenset({'bridleway', 'footway', 'path', 'steps'})
ROAD_HIGHWAYS = frozenset(
    {
        'bus_guideway',
        'cycleway',
        'living_street',
        'primary',
        'primary_link',
        'residential',
        'road',
        'secondary',
        'secondary_link',
        'service',
        'tertiary',
        'tertiary_link',
        'unclassified',
    }
)
EXCLUDED_HIGHWAYS = frozenset(
    {
        'construction',
        'escape',
        'motorway',
        'motorway_link',
        'proposed',
        'raceway',
        'services',
        'trunk',
        'trunk_link',
    }
)
REFERENCE_RAILWAYS = frozenset({'abandoned', 'disused', 'razed'})
POSITIVE_FOOT_VALUES = frozenset({'designated', 'official', 'permissive', 'yes'})
NEGATIVE_ACCESS_VALUES = frozenset({'no', 'private'})
NEGATIVE_FOOT_VALUES = frozenset({'no', 'private', 'use_sidepath'})
