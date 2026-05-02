"""Контракт CLI-команды."""

import argparse
from typing import Protocol


class CliCommand(Protocol):
    """Команда, регистрируемая в общем CLI."""

    name: str
    help: str

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Добавить аргументы команды в parser."""

    def run(self, args: argparse.Namespace) -> int:
        """Выполнить команду и вернуть process exit code."""
