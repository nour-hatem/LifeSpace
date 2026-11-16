"""Integration tests for the database readiness helper."""

from sqlalchemy.engine import make_url

from lifespace.infrastructure.db import check_database, create_engine
from tests.integration.conftest import require_test_database_url


async def test_check_database_is_true_for_test_database() -> None:
    url = await require_test_database_url()
    engine = create_engine(url)
    try:
        assert await check_database(engine) is True
    finally:
        await engine.dispose()


async def test_check_database_is_false_with_wrong_password() -> None:
    url = await require_test_database_url()
    wrong_password_url = make_url(url).set(password="wrong_password_for_test")
    engine = create_engine(wrong_password_url.render_as_string(hide_password=False))
    try:
        assert await check_database(engine) is False
    finally:
        await engine.dispose()
