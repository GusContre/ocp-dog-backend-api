import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_FALLBACK_FILE = Path(__file__).with_name("seed_dogs.json")


class LocalDogCatalog:
    """Loads fallback dog data from a JSON file for offline scenarios."""

    def __init__(self, path: Optional[str] = None) -> None:
        candidate = path or os.getenv("DOG_FALLBACK_FILE")
        self.path = Path(candidate) if candidate else DEFAULT_FALLBACK_FILE
        self._cache: Optional[List[Dict[str, Any]]] = None

    def _load_file(self) -> List[Dict[str, Any]]:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return [
                {"name": (item.get("name") or "").strip() or None,
                 "image": (item.get("image") or "").strip() or None}
                for item in data
                if isinstance(item, dict)
            ]
        except FileNotFoundError:
            return []
        except Exception:
            # If the file is malformed, fall back to an empty dataset.
            return []

    @property
    def items(self) -> List[Dict[str, Any]]:
        if self._cache is None:
            self._cache = [
                item for item in self._load_file() if item.get("name") or item.get("image")
            ]
        return self._cache

    def random(self) -> Optional[Dict[str, Any]]:
        if not self.items:
            return None
        return random.choice(self.items)

    def enumerated(self) -> List[Dict[str, Any]]:
        return [
            {"id": idx + 1, "name": item.get("name"), "image": item.get("image")}
            for idx, item in enumerate(self.items)
        ]
