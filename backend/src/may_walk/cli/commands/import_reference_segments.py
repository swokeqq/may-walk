"""Команда импорта подготовленного OSM-слоя опорных сегментов."""

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from may_walk.services.reference_segments.storage import ImportResult


class ImportReferenceSegmentsCommand:
    """Импортировать подготовленный OSM-слой опорных сегментов."""

    name = 'import-reference-segments'
    help = 'загрузить подготовленный OSM-слой опорных сегментов'

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Добавить аргументы команды."""
        parser.add_argument(
            '--file',
            type=Path,
            required=True,
            help='путь к GeoJSON или GeoJSONSeq файлу',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='заменить существующий слой reference_segment',
        )

    def run(self, args: argparse.Namespace) -> int:
        """Импортировать подготовленный OSM-слой."""
        from may_walk.db.session import SessionLocal
        from may_walk.services.reference_segments.imports import (
            parse_reference_segments_file,
        )
        from may_walk.services.reference_segments.storage import load_reference_segments

        parse_result = parse_reference_segments_file(args.file)
        with SessionLocal() as session:
            import_result = load_reference_segments(
                session,
                parse_result,
                replace=args.replace,
            )
            session.commit()

        self._print_import_result(import_result)
        return 0

    def _print_import_result(self, import_result: 'ImportResult') -> None:
        """Вывести результат импорта опорных сегментов."""
        from may_walk.services.reference_segments.surface_classes import (
            SURFACE_CLASS_VALUES,
        )

        print('Опорные сегменты импортированы')
        print(f'Сегментов добавлено: {import_result.inserted_segment_count}')
        print(f'Объектов пропущено: {import_result.skipped_feature_count}')
        print('Сегменты по покрытиям:')
        for surface_class in SURFACE_CLASS_VALUES:
            count = import_result.surface_class_counts.get(surface_class, 0)
            print(f'- {surface_class}: {count}')
