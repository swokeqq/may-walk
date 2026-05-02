"""Запуск CLI-приложения."""

import argparse
import sys

from may_walk.cli.registry import register_commands


def main() -> int:
    """Выполнить CLI-команду."""
    parser = argparse.ArgumentParser(prog='python -m may_walk.cli')
    subparsers = parser.add_subparsers(dest='command', required=True)
    register_commands(subparsers)

    args = parser.parse_args()
    try:
        return args.command_handler.run(args)
    except ValueError as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 1
