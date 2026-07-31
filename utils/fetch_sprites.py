#!/usr/bin/env python3
"""
Fetch every Pokemon sprite the game can display.

Walks POKEMON_DATA (plus evolution targets and trainer teams defined in the map
JSON) and downloads the front + back sprite for each species, so no Pokemon ever
falls back to the placeholder pokeball.

Usage:
    python -m utils.fetch_sprites
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.downloader import SpriteDownloader


def collect_species_ids() -> list:
    """Every species ID that can appear in battle."""
    from src.pokemon import POKEMON_DATA

    ids = set(POKEMON_DATA.keys())

    # Evolution targets/sources referenced by the data
    for data in POKEMON_DATA.values():
        for key in ("evolves_to", "evolves_from"):
            evo = data.get(key)
            if evo and evo.get("species_id"):
                ids.add(evo["species_id"])

    # Trainer teams from map data (may reference species by id or name)
    name_to_id = {d["name"].lower(): sid for sid, d in POKEMON_DATA.items()}
    map_dir = os.path.join("assets", "maps")
    if os.path.isdir(map_dir):
        for filename in os.listdir(map_dir):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(map_dir, filename), encoding="utf-8") as f:
                try:
                    map_data = json.load(f)
                except json.JSONDecodeError:
                    continue
            for npc in map_data.get("npcs", []):
                trainer = npc.get("trainer_data") or {}
                for entry in trainer.get("team", []):
                    sid = entry.get("species_id")
                    if sid is None and entry.get("species"):
                        sid = name_to_id.get(entry["species"].lower())
                    if sid:
                        ids.add(sid)

    return sorted(ids)


def main():
    ids = collect_species_ids()
    print(f"Fetching front + back sprites for {len(ids)} species: {ids}")

    downloader = SpriteDownloader()
    missing = []
    for species_id in ids:
        for back in (False, True):
            if downloader.get_sprite_path(species_id, back=back) is None:
                missing.append(f"{species_id}{'_back' if back else '_normal'}")

    if missing:
        print(f"\nStill missing ({len(missing)}): {', '.join(missing)}")
    else:
        print("\nAll sprites present.")


if __name__ == "__main__":
    main()
