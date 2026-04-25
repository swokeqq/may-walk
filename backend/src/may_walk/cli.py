"""CLI-команды для операционного управления backend."""

import argparse
import getpass
import sys


def _read_admin_password() -> str:
    """Получить пароль администратора из интерактивного ввода."""
    password = getpass.getpass('Пароль администратора: ')
    password_confirmation = getpass.getpass('Повторите пароль администратора: ')
    if password != password_confirmation:
        raise ValueError('Пароли не совпадают')

    return password


def _create_admin() -> int:
    """Создать первого и единственного администратора."""
    from may_walk.db.session import SessionLocal
    from may_walk.services.admin import create_admin as create_admin_service

    password = _read_admin_password()

    with SessionLocal() as session:
        create_admin_service(session, password)
        session.commit()

    print('Администратор создан')
    return 0


def main() -> int:
    """Выполнить CLI-команду."""
    parser = argparse.ArgumentParser(prog='python -m may_walk.cli')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('create-admin', help='создать первого администратора')

    args = parser.parse_args()
    try:
        if args.command == 'create-admin':
            return _create_admin()
    except ValueError as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 1

    parser.error('Неизвестная команда')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
