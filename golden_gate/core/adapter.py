"""The adapter contract every device adapter implements.

Core (registry, job queue, HTTP API) talks to devices only through this
interface, so core and adapters can be built and tested independently.
Change this file only through a PR that Richard reviews.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Literal

# progress(fraction 0.0-1.0, short message) -> awaitable
Progress = Callable[[float, str], Awaitable[None]]

LinkKind = Literal["wifi_ap", "ble"]


class DeviceState(str, Enum):
    OFFLINE = "offline"
    CONNECTING = "connecting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


@dataclass(frozen=True)
class InputSpec:
    """One input of an action, for API validation and generated UI forms."""

    name: str
    type: Literal["upload", "int", "float", "str", "bool"]
    required: bool = True
    default: Any = None
    min: float | None = None
    max: float | None = None
    help: str = ""


@dataclass(frozen=True)
class ActionSpec:
    """An action a device offers. confirm=True: the UI must ask first
    (anything that uses consumables such as film, or changes device settings)."""

    label: str
    inputs: tuple[InputSpec, ...] = ()
    confirm: bool = False
    help: str = ""


class AdapterError(Exception):
    """A device-level failure with a message safe to show in the UI
    (never include PINs, keys or other secrets)."""


@dataclass
class DeviceConfig:
    """One entry from devices.toml plus its secrets (never logged or returned by the API)."""

    id: str
    kind: str
    name: str
    settings: dict[str, Any] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict, repr=False)


class Adapter:
    """Base class. Subclasses set kind/link/actions and implement the four coroutines."""

    kind: str = ""
    link: LinkKind = "wifi_ap"
    actions: dict[str, ActionSpec] = {}

    def __init__(self, config: DeviceConfig):
        self.config = config

    async def connect(self) -> None:
        """Open the device session (the link itself is already up). Raise AdapterError on failure."""
        raise NotImplementedError

    async def disconnect(self) -> None:
        """Close the device session. Must be safe to call when not connected."""
        raise NotImplementedError

    async def status(self) -> dict[str, Any]:
        """Adapter-specific status fields (e.g. battery, prints_remaining). JSON-serialisable."""
        raise NotImplementedError

    async def run(self, action: str, inputs: dict[str, Any], progress: Progress) -> dict[str, Any]:
        """Run one action with validated inputs. Report progress; return a JSON-serialisable result."""
        raise NotImplementedError
