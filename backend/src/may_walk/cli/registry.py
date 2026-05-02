"""Регистрация CLI-команд."""

import argparse

from may_walk.cli.commands.create_admin import CreateAdminCommand
from may_walk.cli.commands.import_reference_segments import (
    ImportReferenceSegmentsCommand,
)
from may_walk.cli.protocol import CliCommand

COMMANDS: tuple[CliCommand, ...] = (
    CreateAdminCommand(),
    ImportReferenceSegmentsCommand(),
)


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Зарегистрировать все доступные CLI-команды."""
    for command in COMMANDS:
        parser = subparsers.add_parser(command.name, help=command.help)
        command.configure(parser)
        parser.set_defaults(command_handler=command)
