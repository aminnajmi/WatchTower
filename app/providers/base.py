from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Release:
    slug: str
    name: str
    version: str
    release_date: str | None
    source_url: str
    release_type: str = "stable"
    is_rolling: bool = False


class Provider(ABC):
    @abstractmethod
    async def latest(self) -> Release:
        raise NotImplementedError
