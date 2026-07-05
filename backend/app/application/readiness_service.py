"""Readiness probe orchestration."""

import socket

from app.infrastructure.health_checks import HealthChecks
from app.schemas.health import ReadyResponse


class ReadinessService:
    """Run configured dependency checks and return a readiness summary."""

    def __init__(
        self,
        health_checks: HealthChecks | None = None,
        instance_id: str = "",
    ) -> None:
        self._health_checks = health_checks or HealthChecks()
        self.instance_id = instance_id or socket.gethostname()

    async def check(self) -> ReadyResponse:
        """Execute all dependency checks and compose the readiness response."""
        results = await self._health_checks.all_checks()
        overall = "ready" if all(results.values()) else "not_ready"
        status_for = {name: "ok" if value else "error" for name, value in results.items()}
        dependencies: dict[str, str] = {
            "postgresql": status_for["postgres"],
            "qdrant": status_for["qdrant"],
            "minio": status_for["minio"],
            "tensorrtRuntime": status_for["runtime"],
        }
        return ReadyResponse(
            status=overall,
            instanceId=self.instance_id,
            dependencies=dependencies,
        )
