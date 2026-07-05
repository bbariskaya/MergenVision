"""Qdrant vector store for face embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.core.config import Settings, get_settings
from app.core.errors import VectorStoreError
from app.infrastructure.qdrant_client import get_qdrant_client


@dataclass(frozen=True)
class SearchHit:
    id: UUID
    score: float
    payload: dict[str, Any]


def collection_name(
    model_name: str, dimension: int, version: str, prefix: str = "face_samples"
) -> str:
    """Return the normalized Qdrant collection name for a model."""
    safe_name = model_name.replace(".", "_").replace("-", "_")
    return f"{prefix}_{safe_name}_{dimension}_{version}"


class VectorStore:
    """Manages embedding collections and search."""

    def __init__(
        self,
        client: AsyncQdrantClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._client = client or get_qdrant_client(settings)
        self._settings = settings or get_settings()

    def _collection_name(self, model_name: str, dimension: int, version: str) -> str:
        return collection_name(
            model_name,
            dimension,
            version,
            prefix=self._settings.qdrant_collection_prefix,
        )

    async def ensure_collection(
        self,
        model_name: str,
        dimension: int,
        version: str,
    ) -> str:
        """Create the collection if it does not exist and return its name."""
        name = self._collection_name(model_name, dimension, version)
        await self.ensure_collection_name(name, dimension)
        return name

    async def ensure_collection_name(self, name: str, dimension: int) -> None:
        """Create the collection and its payload indexes if missing."""
        try:
            exists = await self._client.collection_exists(name)
            if not exists:
                await self._client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="faceId",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="personId",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="photoId",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="identityType",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=name,
                    field_name="isActive",
                    field_schema=models.PayloadSchemaType.BOOL,
                )
        except Exception as exc:
            raise VectorStoreError(f"Failed to ensure collection {name}: {exc}") from exc

    async def upsert_batch(
        self,
        points: list[dict[str, Any]],
        batch_size: int = 500,
    ) -> None:
        """Upsert a batch of points into the collection inferred from payload.

        The collection name is derived from the first point's payload fields
        ``modelName``, ``embeddingDimension`` and ``modelVersion``. Points are
        chunked into ``batch_size`` slices before calling Qdrant.
        """
        if not points:
            return

        first_payload = points[0].get("payload", {})
        model_name = str(first_payload.get("modelName", ""))
        version = str(first_payload.get("modelVersion", ""))
        dimension = int(first_payload.get("embeddingDimension", 0))
        name = self._collection_name(model_name, dimension, version)
        await self.ensure_collection_name(name, dimension)

        point_structs = [
            models.PointStruct(
                id=str(point["id"]),
                vector=point["vector"].tolist()
                if isinstance(point["vector"], np.ndarray)
                else point["vector"],
                payload=point["payload"],
            )
            for point in points
        ]

        try:
            for i in range(0, len(point_structs), batch_size):
                chunk = point_structs[i : i + batch_size]
                await self._client.upsert(collection_name=name, points=chunk)
        except Exception as exc:
            raise VectorStoreError(f"Failed to upsert into {name}: {exc}") from exc

    async def search(
        self,
        model_name: str,
        dimension: int,
        version: str,
        embedding: np.ndarray,
        top_k: int,
        active_only: bool = True,
    ) -> list[SearchHit]:
        """Search the nearest vectors and return hits."""
        name = await self.ensure_collection(model_name, dimension, version)
        query_filter = None
        if active_only:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="isActive",
                        match=models.MatchValue(value=True),
                    )
                ]
            )
        try:
            vector = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            response = await self._client.query_points(
                collection_name=name,
                query=vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
            results = response.points
        except Exception as exc:
            raise VectorStoreError(f"Failed to search {name}: {exc}") from exc

        return [
            SearchHit(
                id=UUID(str(point.id)),
                score=float(point.score),
                payload=point.payload or {},
            )
            for point in results
        ]


def get_vector_store(
    client: AsyncQdrantClient | None = None,
    settings: Settings | None = None,
) -> VectorStore:
    return VectorStore(client=client, settings=settings)
