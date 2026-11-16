"""Integration tests for the database readiness helper."""

from sqlalchemy.engine import make_url

from lifespace.infrastructure.db import check_database, create_engine


async def test_check_database_is_true_for_test_database(test_database_url: str) -> None:
    engine = create_engine(test_database_url)
    try:
        assert await check_database(engine) is True
    finally:
        await engine.dispose()


async def test_check_database_is_false_with_wrong_password(test_database_url: str) -> None:
    url = make_url(test_database_url).set(password="wrong_password_for_test")
    engine = create_engine(url.render_as_string(hide_password=False))
    try:
        assert await check_database(engine) is False
    finally:
        await engine.dispose()
