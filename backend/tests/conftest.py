"""Общие фикстуры для тестов."""

import pytest
from fastapi.testclient import TestClient

from may_walk.main import app


@pytest.fixture
def client() -> TestClient:
    """Создать тестовый HTTP-клиент для приложения."""
    return TestClient(app, base_url='https://testserver')
