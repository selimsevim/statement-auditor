"""Configuration loading.

Reads config.yaml from the repo root, resolves relative paths to absolute, and
provides typed access. The Anthropic API key is read from the environment only.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


class Config:
    """Thin typed wrapper over config.yaml with path resolution."""

    def __init__(self, data: dict[str, Any], root: Path) -> None:
        self._data = data
        self.root = root

    # --- raw sections ---
    @property
    def models(self) -> dict[str, str]:
        return self._data["models"]

    @property
    def thresholds(self) -> dict[str, float]:
        return self._data["thresholds"]

    @property
    def llm(self) -> dict[str, Any]:
        return self._data["llm"]

    @property
    def hedge_lexicon(self) -> list[str]:
        return list(self._data["hedge_lexicon"])

    @property
    def pricing(self) -> dict[str, dict[str, float]]:
        """Per-model $/1M-token pricing. Optional; used only by the scorer diff."""
        return self._data.get("pricing", {})

    # --- resolved paths ---
    def path(self, key: str) -> Path:
        """Absolute path for a `paths.<key>` entry (relative to repo root)."""
        p = Path(self._data["paths"][key])
        return p if p.is_absolute() else (self.root / p)

    def ensure_dirs(self) -> None:
        """Create the data directories the pipeline writes to."""
        for key in ("raw_dir", "text_dir", "cache_dir"):
            self.path(key).mkdir(parents=True, exist_ok=True)
        self.path("db_path").parent.mkdir(parents=True, exist_ok=True)


def _load_dotenv(root: Path) -> None:
    """Load KEY=VALUE lines from a repo-root .env into the environment.

    Zero-dependency and non-overriding: real environment variables always win,
    so a .env is just a convenience for local runs. The file is gitignored; the
    key is never hardcoded in source.
    """
    env_file = root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path: Path | str | None = None) -> Config:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    root = cfg_path.resolve().parent
    _load_dotenv(root)
    with open(cfg_path) as f:
        data = yaml.safe_load(f)
    return Config(data, root)


def require_api_key() -> str:
    """Return the Anthropic API key from the environment, or raise with guidance."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Provide it either by exporting it "
            "(`export ANTHROPIC_API_KEY=sk-ant-...`) or by creating a gitignored "
            "`.env` file at the repo root containing:\n"
            "    ANTHROPIC_API_KEY=sk-ant-..."
        )
    return key
