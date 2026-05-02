"""Команда создания первого администратора."""

import argparse
import getpass


class CreateAdminCommand:
    """Создать первого и единственного администратора."""

    name = 'create-admin'
    help = 'создать первого администратора'

    def configure(self, _parser: argparse.ArgumentParser) -> None:
        """Добавить аргументы команды."""

    def run(self, _args: argparse.Namespace) -> int:
        """Создать администратора."""
        from may_walk.db.session import SessionLocal
        from may_walk.services.admin import create_admin as create_admin_service

        password = self._read_admin_password()

        with SessionLocal() as session:
            create_admin_service(session, password)
            session.commit()

        print('Администратор создан')
        return 0

    def _read_admin_password(self) -> str:
        """Получить пароль администратора из интерактивного ввода."""
        password = getpass.getpass('Пароль администратора: ')
        password_confirmation = getpass.getpass('Повторите пароль администратора: ')
        if password != password_confirmation:
            raise ValueError('Пароли не совпадают')

        return password
