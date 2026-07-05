"""Shared Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ListingResponse[T](BaseModel):
    """Generic paginated list response."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[T]
    total: int
    limit: int
    offset: int
