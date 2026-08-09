from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class IntegrationStatus(str, Enum):
    PRODUCTION = "production"
    FUNCTIONAL = "functional"
    PARTIAL = "partial"
    BLOCKED_BY_CREDENTIALS = "blocked_by_credentials"
    BLOCKED_BY_EXTERNAL_SETUP = "blocked_by_external_setup"
    PLANNED = "planned"


@dataclass(frozen=True)
class IntegrationDescriptor:
    id: str
    name: str
    status: IntegrationStatus
    required_environment: tuple[str, ...] = ()


class IntegrationAdapter(ABC):
    descriptor: IntegrationDescriptor

    @abstractmethod
    def healthcheck(self) -> dict:
        raise NotImplementedError
