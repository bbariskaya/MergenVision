"""Unit tests for StatsService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.stats_service import StatsService
from app.domain.models import Person


@pytest.fixture
def service():
    session = MagicMock()
    return StatsService(session=session)


@pytest.mark.asyncio
async def test_summary_counts_all_entities(service):
    async def _execute(stmt):
        result = MagicMock()
        # SQLAlchemy scalar for count.
        result.scalar.return_value = 7
        return result

    service._session.execute = _execute

    data = await service.summary()

    assert data == {
        "personCount": 7,
        "photoCount": 7,
        "faceSampleCount": 7,
        "identificationRequestCount": 7,
    }


@pytest.mark.asyncio
async def test_get_alias_returns_summary(service):
    async def _execute(stmt):
        result = MagicMock()
        result.scalar.return_value = 3
        return result

    service._session.execute = _execute

    data = await service.get()

    assert data["personCount"] == 3


@pytest.mark.asyncio
async def test_count_uses_count_statement(service):
    async def _execute(stmt):
        result = MagicMock()
        result.scalar.return_value = 0
        # Verify the statement counts the Person table.
        assert "from person" in str(stmt).lower()
        return result

    service._session.execute = _execute

    await service._count(Person)
