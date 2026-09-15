from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, TypeVar

from src.loader import load_likes, load_mutes, load_tweets, load_user_list
from src.models import AppConfig

T = TypeVar("T")


@dataclass(frozen=True)
class InputState(Generic[T]):
    name: str
    path: str
    required: bool
    status: str
    data: T | None = None
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.status in {"ready", "valid_empty", "optional_missing"}


def _read(name: str, path: str, required: bool, loader: Callable[[str], T]) -> InputState[T]:
    if not Path(path).is_file():
        status = "missing_required" if required else "optional_missing"
        return InputState(name, path, required, status)
    try:
        data = loader(path)
    except Exception as exc:
        return InputState(name, path, required, "invalid", error=f"{type(exc).__name__}: {exc}")
    return InputState(name, path, required, "ready" if data else "valid_empty", data=data)


def evaluate_inputs(config: AppConfig) -> dict[str, InputState]:
    """Return the single startup/analysis readiness authority.

    Tweets are the required analysis source. Relationship, like and mute exports are
    optional enrichments; their absence never disguises a missing/invalid tweets file.
    """
    files = config.files
    return {
        "tweets": _read("tweets", files.tweets, True, load_tweets),
        "follower": _read("follower", files.follower, False, load_user_list),
        "following": _read("following", files.following, False, load_user_list),
        "like": _read("like", files.like, False, load_likes),
        "mute": _read("mute", files.mute, False, load_mutes),
    }


def required_inputs_ready(states: dict[str, InputState]) -> bool:
    return all(state.ready for state in states.values() if state.required)
