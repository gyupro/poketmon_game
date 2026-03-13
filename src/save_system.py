"""
Save/Load System - Handles game state persistence with atomic writes and validation.
"""

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class SaveData:
    """Represents a complete game save state."""

    version: int = 1
    player_name: str = ""
    player_x: int = 10
    player_y: int = 10
    map_id: str = "pallet_town"
    facing: str = "down"
    team: List[dict] = field(default_factory=list)
    bag: Dict[str, int] = field(default_factory=dict)
    money: int = 3000
    badges: List[str] = field(default_factory=list)
    pokedex_seen: List[str] = field(default_factory=list)
    pokedex_caught: List[str] = field(default_factory=list)
    play_time: float = 0.0
    event_flags: Dict[str, bool] = field(default_factory=dict)
    defeated_trainers: List[str] = field(default_factory=list)
    last_healed_map: str = "pallet_town"
    last_healed_x: int = 10
    last_healed_y: int = 10

    @classmethod
    def new_game(cls, name: str, starter_id: str) -> "SaveData":
        """Create a new game save with the chosen starter Pokemon."""
        starter = {
            "name": starter_id,
            "level": 5,
            "hp": 20,
            "max_hp": 20,
            "moves": [],
        }
        return cls(
            player_name=name,
            team=[starter],
            bag={"potion": 5, "pokeball": 5},
            pokedex_seen=[starter_id],
            pokedex_caught=[starter_id],
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SaveData":
        """Deserialize from a plain dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SaveSystem:
    """Manages save file I/O with atomic writes and data validation."""

    def __init__(self, save_dir: str = "saves") -> None:
        self._save_dir = save_dir
        os.makedirs(self._save_dir, exist_ok=True)

    def _slot_path(self, slot: int) -> str:
        return os.path.join(self._save_dir, f"slot_{slot}.json")

    def has_save(self, slot: int) -> bool:
        """Return True if a save file exists for the given slot."""
        return os.path.isfile(self._slot_path(slot))

    def save(self, slot: int, data: SaveData) -> None:
        """Persist save data atomically (write to .tmp then replace)."""
        final_path = self._slot_path(slot)
        tmp_path = final_path + ".tmp"
        payload = data.to_dict()
        with open(tmp_path, "w") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, final_path)

    def save_async(self, slot: int, data: SaveData) -> threading.Thread:
        """Non-blocking save via a background thread."""
        thread = threading.Thread(target=self.save, args=(slot, data), daemon=True)
        thread.start()
        return thread

    def load(self, slot: int) -> Optional[SaveData]:
        """Load and validate save data. Returns None if the slot has no save."""
        path = self._slot_path(slot)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
        data = SaveData.from_dict(raw)
        self._validate(data)
        return data

    def get_slot_info(self, slot: int) -> Optional[dict]:
        """Return a summary dictionary for menu display, or None."""
        data = self.load(slot)
        if data is None:
            return None
        return {
            "player_name": data.player_name,
            "map_id": data.map_id,
            "badges": len(data.badges),
            "team_size": len(data.team),
            "play_time": data.play_time,
            "money": data.money,
        }

    @staticmethod
    def _validate(data: SaveData) -> None:
        """Clamp invalid values so loaded data is always safe to use."""
        if data.money < 0:
            data.money = 0

        for member in data.team:
            max_hp = member.get("max_hp", 1)
            if max_hp < 1:
                member["max_hp"] = 1
                max_hp = 1
            hp = member.get("hp", max_hp)
            if hp < 0:
                member["hp"] = 0
            elif hp > max_hp:
                member["hp"] = max_hp
