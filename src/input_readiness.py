import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from src.config import load_config
from src.loader import load_likes, load_mutes, load_tweets, load_user_list
from src.models import AppConfig

Loader = Callable[[str], Any]

LOADERS: dict[str, Loader] = {
    "tweets": load_tweets,
    "follower": load_user_list,
    "following": load_user_list,
    "like": load_likes,
    "mute": load_mutes,
}


@dataclass(frozen=True)
class InputStatus:
    name: str
    path: str
    required: bool
    status: str
    error: str | None = None


@dataclass
class InputReadiness:
    ready: bool
    inputs: list[InputStatus]
    data: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "inputs": [asdict(item) for item in self.inputs]}


def load_configured_inputs(config: AppConfig) -> InputReadiness:
    required = set(config.required_files)
    configured = config.files.model_dump()
    statuses: list[InputStatus] = []
    data: dict[str, Any] = {}

    unknown_required = sorted(required - configured.keys())
    for name in unknown_required:
        statuses.append(InputStatus(name=name, path="", required=True, status="invalid-config", error="unknown input"))

    for name, path in configured.items():
        is_required = name in required
        loader = LOADERS.get(name)
        if loader is None:
            statuses.append(
                InputStatus(name=name, path=path, required=is_required, status="invalid-config", error="no loader")
            )
            continue
        if not Path(path).is_file():
            statuses.append(
                InputStatus(
                    name=name,
                    path=path,
                    required=is_required,
                    status="missing-required" if is_required else "optional-missing",
                )
            )
            continue
        try:
            value = loader(path)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            statuses.append(
                InputStatus(
                    name=name,
                    path=path,
                    required=is_required,
                    status="invalid",
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        data[name] = value
        status = "valid-empty" if len(value) == 0 else "ready"
        statuses.append(InputStatus(name=name, path=path, required=is_required, status=status))

    ready = not any(item.status in {"missing-required", "invalid", "invalid-config"} for item in statuses)
    return InputReadiness(ready=ready, inputs=statuses, data=data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check configured X archive input readiness")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    result = load_configured_inputs(load_config(args.config))
    print(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
