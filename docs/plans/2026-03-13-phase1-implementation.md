# Phase 1: Core Infrastructure + Viridian City — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add save/load system, split UI into modules, extend map schema, fix encounter tables, implement white-out flow, and add Viridian City with Pokemon Center + Shop.

**Architecture:** JSON-based save system with atomic writes. UI split into 7 focused modules preserving the existing public API. Maps fully data-driven from JSON. New species data for starter evolutions + Rattata.

**Tech Stack:** Python 3.10+, Pygame 2.x, JSON for data, pytest for tests.

**Spec:** `docs/specs/2026-03-13-game-overhaul-design.md` (Phase 1 sections 1A–1G)

---

## File Map

### New Files
| File | Responsibility |
|------|---------------|
| `src/save_system.py` | Save/load JSON with atomic writes, validation, threading |
| `src/shop.py` | Shop data model, buy/sell logic |
| `src/ui/__init__.py` | UI class (facade), UIState, state routing |
| `src/ui/components.py` | Colors, Button, HealthBar, ExperienceBar, TypeBadge, helpers |
| `src/ui/battle_ui.py` | Battle rendering, move select, pokemon info panels |
| `src/ui/menu_ui.py` | Main menu, pause, pokemon team, bag, starter select |
| `src/ui/world_hud.py` | World overlay, location banner, context hints |
| `src/ui/shop_ui.py` | Shop buy/sell interface |
| `src/ui/dialog.py` | Dialog box rendering, typewriter effect |
| `tests/test_save_system.py` | Save/load unit tests |
| `tests/test_shop.py` | Shop logic tests |
| `tests/test_white_out.py` | White-out flow tests |
| `assets/maps/viridian_city.json` | Viridian City map data |

### Modified Files
| File | Changes |
|------|---------|
| `src/game.py` | Import from `src/ui/`, add save triggers, white-out flow, shop state |
| `src/encounters.py` | Replace fantasy encounter tables with lore-accurate ones |
| `src/pokemon.py` | Add species data: Ivysaur(#2), Charmeleon(#5), Wartortle(#8), Rattata(#19) |
| `src/world.py` | Load NPCs/trainers/items/triggers from map JSON |
| `src/map.py` | Remove `create_sample_maps()`, load all maps from JSON |
| `src/items.py` | Add Antidote, add price field to items |
| `src/player.py` | Add money, last_healed_map fields, to_dict/from_dict for save |
| `assets/maps/pallet_town.json` | Add NPC/trainer/trigger data to schema |
| `assets/maps/route_1.json` | Add 2 trainers, items, lore-accurate encounters |

### Deleted Files
| File | Reason |
|------|--------|
| `src/ui.py` | Replaced by `src/ui/` package (content moved, not deleted until split complete) |

---

## Chunk 1: Save System

### Task 1: Save/Load Core

**Files:**
- Create: `src/save_system.py`
- Create: `tests/test_save_system.py`

- [ ] **Step 1: Write failing tests for save/load**

```python
# tests/test_save_system.py
import os
import json
import pytest
from src.save_system import SaveSystem, SaveData

SAVE_DIR = "/tmp/test_pokemon_saves"

@pytest.fixture(autouse=True)
def clean_saves():
    os.makedirs(SAVE_DIR, exist_ok=True)
    yield
    for f in os.listdir(SAVE_DIR):
        os.remove(os.path.join(SAVE_DIR, f))
    os.rmdir(SAVE_DIR)

class TestSaveSystem:
    def test_save_creates_file(self):
        ss = SaveSystem(SAVE_DIR)
        data = SaveData.new_game("Ash", starter_id=4)
        ss.save(0, data)
        assert os.path.exists(os.path.join(SAVE_DIR, "save_0.json"))

    def test_load_returns_saved_data(self):
        ss = SaveSystem(SAVE_DIR)
        data = SaveData.new_game("Ash", starter_id=4)
        data.player_x = 15
        data.player_y = 20
        data.map_id = "route_1"
        ss.save(0, data)
        loaded = ss.load(0)
        assert loaded.player_name == "Ash"
        assert loaded.player_x == 15
        assert loaded.map_id == "route_1"

    def test_save_has_version(self):
        ss = SaveSystem(SAVE_DIR)
        data = SaveData.new_game("Ash", starter_id=4)
        ss.save(0, data)
        with open(os.path.join(SAVE_DIR, "save_0.json")) as f:
            raw = json.load(f)
        assert raw["version"] == 1

    def test_load_nonexistent_returns_none(self):
        ss = SaveSystem(SAVE_DIR)
        assert ss.load(0) is None

    def test_slot_has_save(self):
        ss = SaveSystem(SAVE_DIR)
        assert not ss.has_save(0)
        data = SaveData.new_game("Ash", starter_id=4)
        ss.save(0, data)
        assert ss.has_save(0)

    def test_save_validation_clamps_hp(self):
        ss = SaveSystem(SAVE_DIR)
        data = SaveData.new_game("Ash", starter_id=4)
        # Corrupt the HP to be above max
        data.team[0]["current_hp"] = 9999
        data.team[0]["max_hp"] = 20
        ss.save(0, data)
        loaded = ss.load(0)
        assert loaded.team[0]["current_hp"] <= loaded.team[0]["max_hp"]

    def test_atomic_write_no_partial(self):
        ss = SaveSystem(SAVE_DIR)
        data = SaveData.new_game("Ash", starter_id=4)
        ss.save(1, data)
        # No .tmp files should remain
        tmp_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".tmp")]
        assert len(tmp_files) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/test_save_system.py -v`
Expected: ImportError — `save_system` module not found

- [ ] **Step 3: Implement SaveSystem**

```python
# src/save_system.py
"""Save/load system with atomic writes and validation."""
import json
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class SaveData:
    """All data needed to restore a game session."""
    version: int = 1
    player_name: str = ""
    player_x: int = 10
    player_y: int = 10
    map_id: str = "pallet_town"
    facing: str = "down"
    team: List[Dict[str, Any]] = field(default_factory=list)
    bag: Dict[str, int] = field(default_factory=dict)
    money: int = 3000
    badges: List[str] = field(default_factory=list)
    pokedex_seen: List[int] = field(default_factory=list)
    pokedex_caught: List[int] = field(default_factory=list)
    play_time: float = 0.0
    event_flags: Dict[str, bool] = field(default_factory=dict)
    defeated_trainers: List[str] = field(default_factory=list)
    last_healed_map: str = "pallet_town"
    last_healed_x: int = 10
    last_healed_y: int = 10

    @classmethod
    def new_game(cls, name: str, starter_id: int = 4) -> "SaveData":
        starter = {
            "species_id": starter_id,
            "level": 5,
            "current_hp": 20,
            "max_hp": 20,
            "moves": [],
            "evs": {}, "ivs": {},
            "status": None,
            "nickname": None,
        }
        return cls(
            player_name=name,
            team=[starter],
            bag={"potion": 5, "pokeball": 5},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SaveData":
        d.pop("version", None)
        return cls(version=1, **{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class SaveSystem:
    """Manages save slots with atomic writes."""

    def __init__(self, save_dir: str = "saves"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def _path(self, slot: int) -> str:
        return os.path.join(self.save_dir, f"save_{slot}.json")

    def has_save(self, slot: int) -> bool:
        return os.path.exists(self._path(slot))

    def save(self, slot: int, data: SaveData) -> None:
        """Save data to slot with atomic write."""
        payload = data.to_dict()
        payload["version"] = 1
        tmp_path = self._path(slot) + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp_path, self._path(slot))
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def save_async(self, slot: int, data: SaveData) -> None:
        """Non-blocking save in a background thread."""
        thread = threading.Thread(target=self.save, args=(slot, data), daemon=True)
        thread.start()

    def load(self, slot: int) -> Optional[SaveData]:
        """Load and validate save data from slot."""
        if not self.has_save(slot):
            return None
        try:
            with open(self._path(slot)) as f:
                raw = json.load(f)
            data = SaveData.from_dict(raw)
            self._validate(data)
            return data
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def _validate(self, data: SaveData) -> None:
        """Clamp invalid values to safe defaults."""
        for pkmn in data.team:
            max_hp = pkmn.get("max_hp", 1)
            if max_hp < 1:
                pkmn["max_hp"] = 1
                max_hp = 1
            cur = pkmn.get("current_hp", max_hp)
            pkmn["current_hp"] = max(0, min(cur, max_hp))
        data.money = max(0, data.money)

    def get_slot_info(self, slot: int) -> Optional[Dict[str, Any]]:
        """Get summary info for a save slot (for menu display)."""
        data = self.load(slot)
        if not data:
            return None
        return {
            "name": data.player_name,
            "badges": len(data.badges),
            "play_time": data.play_time,
            "team_size": len(data.team),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/test_save_system.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/save_system.py tests/test_save_system.py
git commit -m "feat: Add save/load system with atomic writes and validation"
```

---

### Task 2: Integrate Save with Game Loop

**Files:**
- Modify: `src/game.py`
- Modify: `src/player.py`

- [ ] **Step 1: Add to_dict/from_dict to Player**

In `src/player.py`, add methods to serialize/deserialize player state for save system. Add `money` and `last_healed_map/x/y` fields.

```python
# Add to Player.__init__:
self.money = 3000
self.last_healed_map = "pallet_town"
self.last_healed_x = 10
self.last_healed_y = 10

# Add methods:
def to_save_data(self) -> dict:
    """Serialize player state for saving."""
    team_data = []
    for p in self.team:
        team_data.append({
            "species_id": p.species_id,
            "level": p.level,
            "current_hp": p.current_hp,
            "max_hp": p.max_hp,
            "moves": [{"name": m.name, "pp": m.current_pp} for m in p.moves],
            "nickname": p.nickname,
            "status": p.status.value if p.status else None,
        })
    return {
        "player_name": self.name,
        "player_x": self.grid_x,
        "player_y": self.grid_y,
        "facing": self.facing,
        "team": team_data,
        "money": self.money,
        "last_healed_map": self.last_healed_map,
        "last_healed_x": self.last_healed_x,
        "last_healed_y": self.last_healed_y,
    }
```

- [ ] **Step 2: Add save triggers to Game**

In `src/game.py`:
- Import `SaveSystem`
- Init `self.save_system = SaveSystem("saves")` in `Game.__init__`
- Add `self.current_slot = 0` and `self.play_time = 0.0`
- In `update()`, accumulate `self.play_time += dt`
- Add `save_game()` method that builds `SaveData` from current state and calls `save_system.save_async()`
- In `world.change_map()` callback (or after `_execute_map_change`), call `save_game()` for auto-save
- Wire pause menu "Save" button to `save_game()` with confirmation message

- [ ] **Step 3: Wire "Continue" button on main menu**

In main menu rendering, check `save_system.has_save(slot)` for each slot. If any save exists, enable "Continue" button. On selection, show slot picker (3 slots with summary info), load selected slot, restore game state.

- [ ] **Step 4: Verify manually — save, quit, reload, continue**

Run: `cd /home/ubuntu/바탕화면/workspace/poketmon_game && python main.py`
- Start new game, select starter, walk around
- Press ESC → Save → confirm save works (check `saves/save_0.json` exists)
- Quit and restart → Continue should load back to same position

- [ ] **Step 5: Commit**

```bash
git add src/game.py src/player.py
git commit -m "feat: Integrate save/load with game loop (auto-save + manual)"
```

---

## Chunk 2: UI Refactor

### Task 3: Split UI into Package

**Files:**
- Create: `src/ui/__init__.py`, `src/ui/components.py`, `src/ui/battle_ui.py`, `src/ui/menu_ui.py`, `src/ui/world_hud.py`, `src/ui/dialog.py`, `src/ui/shop_ui.py`
- Delete: `src/ui.py` (after split)

This is a structural refactor. No behavior changes.

- [ ] **Step 1: Capture visual regression baseline**

Run the screenshot script from earlier to capture reference images of every UI state:
```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -c "
# [same screenshot script as before, saving to /tmp/baseline_*.png]
"
```

- [ ] **Step 2: Create src/ui/ package structure**

Extract from `src/ui.py`:

1. **`components.py`** — `Colors` class, `_draw_rounded_rect`, `_draw_shadow`, `_draw_gradient_rect`, `_draw_type_badge`, `Button` class, `HealthBar` class, `ExperienceBar` class, `PokemonInfoPanel` class, `BattleMenu` class (lines ~30-770)

2. **`battle_ui.py`** — `BattleUI` class with methods: `draw_battle_scene`, `draw_battle_background`, `_draw_battle_content`, `_draw_pokemon_sprite_fallback`, battle-related rendering (extract from UI class)

3. **`menu_ui.py`** — Methods: `draw_main_menu`, `handle_main_menu_events`, `draw_pause_menu`, `handle_pause_events`, `draw_pokemon_menu`, `handle_pokemon_menu_events`, `draw_bag_menu`, `handle_bag_events`, `render_starter_selection` (from game.py)

4. **`world_hud.py`** — Methods: `draw_world_hud`, `show_location`

5. **`dialog.py`** — Dialog box rendering extracted from battle/world contexts

6. **`shop_ui.py`** — Empty placeholder (implemented in Task 6)

7. **`__init__.py`** — `UIState` enum + `UI` class that delegates to sub-modules:

```python
# src/ui/__init__.py
from src.ui.components import Colors, Button, HealthBar, ExperienceBar
from src.ui.battle_ui import BattleUI
from src.ui.menu_ui import MenuUI
from src.ui.world_hud import WorldHUD
from src.ui.dialog import DialogRenderer

class UI:
    """Facade that delegates to specialized UI modules."""
    def __init__(self, screen):
        self.screen = screen
        self.state = UIState.MAIN_MENU
        self.battle_ui = BattleUI(screen)
        self.menu_ui = MenuUI(screen)
        self.world_hud = WorldHUD(screen)
        self.dialog = DialogRenderer(screen)
        # ... preserve all existing public API methods by delegating
```

- [ ] **Step 3: Update imports in game.py**

Change `from src.ui import UI, UIState` to `from src.ui import UI, UIState` — should work unchanged since `__init__.py` re-exports.

- [ ] **Step 4: Run all tests**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/ -v
```
Expected: 12/12 pass

- [ ] **Step 5: Capture regression screenshots and compare**

Run same screenshot script, save to `/tmp/after_*.png`. Visually compare each state matches baseline.

- [ ] **Step 6: Delete old src/ui.py, commit**

```bash
rm src/ui.py
git add src/ui/ src/game.py
git rm src/ui.py
git commit -m "refactor: Split ui.py into src/ui/ package (7 modules)"
```

---

## Chunk 3: Encounter Tables + Species Data + White-Out

### Task 4: Fix Encounter Tables

**Files:**
- Modify: `src/encounters.py`

- [ ] **Step 1: Replace encounter tables**

Replace the entire encounter table data with lore-accurate tables per spec section 1D. Remove Safari Zone, Victory Road, Power Plant, Seafoam, Cerulean Cave, Faraway Island tables.

Route 1: Pidgey (Lv.2-5 Common), Rattata (Lv.2-4 Common)
Route 2: Pidgey (Lv.3-6), Rattata (Lv.3-5), Caterpie (Lv.3-5 Uncommon)
(Leave Viridian Forest, Route 3, Mt. Moon as placeholder empty tables for future phases)

- [ ] **Step 2: Run encounter tests**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/test_encounters.py -v
```
Fix any tests that relied on old fantasy encounter tables.

- [ ] **Step 3: Commit**

```bash
git add src/encounters.py tests/test_encounters.py
git commit -m "fix: Replace fantasy encounter tables with lore-accurate Gen 1 data"
```

### Task 5: Add New Species Data

**Files:**
- Modify: `src/pokemon.py`

- [ ] **Step 1: Add Ivysaur (#2), Charmeleon (#5), Wartortle (#8), Rattata (#19)**

Add to `POKEMON_DATA` dict with Gen 1 accurate base stats, types, learnsets, and evolution data. Each entry needs: name, id, types, base_stats, abilities, learnset, evolves_to/evolves_from.

Example Rattata:
```python
19: {
    "name": "Rattata", "id": 19,
    "types": ["normal"],
    "base_stats": {"hp": 30, "attack": 56, "defense": 35, "sp_attack": 25, "sp_defense": 35, "speed": 72},
    "abilities": [{"name": "Run Away", "description": "Enables sure getaway from wild Pokemon."}],
    "learnset": [
        {"level": 1, "move": "Tackle"}, {"level": 1, "move": "Tail Whip"},
        {"level": 4, "move": "Quick Attack"}, {"level": 7, "move": "Focus Energy"},
        {"level": 10, "move": "Bite"}, {"level": 13, "move": "Pursuit"},
    ],
    "evolves_to": {"species_id": 20, "level": 20},
    "experience_group": "medium_fast",
}
```

Also add evolution data to existing starters (Bulbasaur→Ivysaur@16, Charmander→Charmeleon@16, Squirtle→Wartortle@16).

- [ ] **Step 2: Verify imports work**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -c "
from src.pokemon import create_pokemon_from_species
for sid in [2, 5, 8, 19]:
    p = create_pokemon_from_species(sid, 10)
    print(f'{p.species_name} Lv.{p.level} HP:{p.max_hp}')
"
```

- [ ] **Step 3: Commit**

```bash
git add src/pokemon.py
git commit -m "feat: Add species data for Ivysaur, Charmeleon, Wartortle, Rattata"
```

### Task 6: White-Out Flow

**Files:**
- Modify: `src/game.py`
- Create: `tests/test_white_out.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_white_out.py
from src.player import Player
from src.pokemon import create_pokemon_from_species

class TestWhiteOut:
    def test_all_fainted_detected(self):
        player = Player("Ash", 10, 10)
        pkmn = create_pokemon_from_species(4, 5)
        pkmn.current_hp = 0
        player.team = [pkmn]
        assert player.all_fainted()

    def test_not_all_fainted(self):
        player = Player("Ash", 10, 10)
        pkmn = create_pokemon_from_species(4, 5)
        player.team = [pkmn]
        assert not player.all_fainted()

    def test_money_halved_on_whiteout(self):
        player = Player("Ash", 10, 10)
        player.money = 1000
        player.apply_whiteout_penalty()
        assert player.money == 500

    def test_money_floor_zero(self):
        player = Player("Ash", 10, 10)
        player.money = 1
        player.apply_whiteout_penalty()
        assert player.money == 0
```

- [ ] **Step 2: Implement all_fainted() and apply_whiteout_penalty() in Player**

```python
def all_fainted(self) -> bool:
    return len(self.team) > 0 and all(p.current_hp <= 0 for p in self.team)

def apply_whiteout_penalty(self) -> None:
    self.money = self.money // 2
```

- [ ] **Step 3: Add white-out flow in Game.end_battle()**

After battle ends, if `player.all_fainted()`:
- Show message "{name} is out of usable Pokemon!"
- Fade to black
- `player.apply_whiteout_penalty()`
- Heal all team Pokemon to full HP
- Teleport to `player.last_healed_map` at `last_healed_x/y`
- Transition to world state

- [ ] **Step 4: Run tests**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/test_white_out.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/player.py src/game.py tests/test_white_out.py
git commit -m "feat: Add white-out flow (teleport to last Pokemon Center, halve money)"
```

---

## Chunk 4: Viridian City + Shop

### Task 7: Shop System

**Files:**
- Create: `src/shop.py`
- Create: `tests/test_shop.py`
- Modify: `src/items.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_shop.py
from src.shop import Shop, ShopItem

class TestShop:
    def test_buy_deducts_money(self):
        shop = Shop([ShopItem("potion", 300)])
        bag = {"potion": 0}
        money = shop.buy("potion", 1, 1000, bag)
        assert money == 700
        assert bag["potion"] == 1

    def test_buy_insufficient_funds(self):
        shop = Shop([ShopItem("potion", 300)])
        bag = {}
        money = shop.buy("potion", 1, 100, bag)
        assert money == 100  # unchanged
        assert bag.get("potion", 0) == 0

    def test_sell_gives_half_price(self):
        shop = Shop([ShopItem("potion", 300)])
        bag = {"potion": 3}
        money = shop.sell("potion", 1, 500, bag, sell_price=150)
        assert money == 650
        assert bag["potion"] == 2

    def test_buy_multiple(self):
        shop = Shop([ShopItem("pokeball", 200)])
        bag = {}
        money = shop.buy("pokeball", 5, 2000, bag)
        assert money == 1000
        assert bag["pokeball"] == 5
```

- [ ] **Step 2: Implement Shop**

```python
# src/shop.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ShopItem:
    item_id: str
    price: int

class Shop:
    def __init__(self, inventory: List[ShopItem]):
        self.inventory = {item.item_id: item for item in inventory}

    def buy(self, item_id: str, quantity: int, money: int, bag: Dict[str, int]) -> int:
        item = self.inventory.get(item_id)
        if not item:
            return money
        total = item.price * quantity
        if total > money:
            return money
        bag[item_id] = bag.get(item_id, 0) + quantity
        return money - total

    def sell(self, item_id: str, quantity: int, money: int, bag: Dict[str, int], sell_price: int = 0) -> int:
        current = bag.get(item_id, 0)
        if current < quantity:
            return money
        bag[item_id] = current - quantity
        return money + (sell_price * quantity)
```

- [ ] **Step 3: Add prices to items.py**

Add `price` field to item data. Potion: 300, Super Potion: 700, Poke Ball: 200, Antidote: 100.

- [ ] **Step 4: Run tests**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/test_shop.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/shop.py src/items.py tests/test_shop.py
git commit -m "feat: Add shop system with buy/sell logic"
```

### Task 8: Viridian City Map

**Files:**
- Create: `assets/maps/viridian_city.json`
- Modify: `assets/maps/route_1.json` (add north exit warp to Viridian)
- Modify: `src/world.py` (load new map)

- [ ] **Step 1: Design Viridian City map (40x40)**

Create JSON map with:
- Pokemon Center (8x6 building, left side)
- Poke Mart (6x5 building, right side)
- 3-4 houses
- Paths connecting buildings
- South exit → Route 1
- North exit → Route 2 (blocked for now with NPC "The road ahead is closed")
- NPCs: Nurse Joy (healer), Shopkeeper, 3-4 townspeople with dialog
- Tall grass patches on edges

- [ ] **Step 2: Add warp connections**

Route 1 north edge (y=0) → Viridian City south edge
Viridian City south edge → Route 1 north

- [ ] **Step 3: Implement Pokemon Center healing**

When player interacts with Nurse Joy NPC (action: "heal"):
- Dialog: "Welcome! Let me heal your Pokemon."
- Flash animation
- Heal all team Pokemon to full HP
- Set `player.last_healed_map` to current map
- Dialog: "Your Pokemon are all better now!"

- [ ] **Step 4: Implement Shop NPC**

When player interacts with Shopkeeper NPC (action: "shop"):
- Open shop UI with Viridian City inventory
- Items: Poke Ball ($200), Potion ($300), Antidote ($100)

- [ ] **Step 5: Test navigation Pallet→Route1→Viridian**

Run game, walk from Pallet Town through Route 1 to Viridian City. Verify:
- Map transition works
- NPCs render and are interactable
- Healing works
- Shop works

- [ ] **Step 6: Commit**

```bash
git add assets/maps/ src/world.py src/game.py
git commit -m "feat: Add Viridian City map with Pokemon Center and Shop"
```

### Task 9: Route 1 Trainers

**Files:**
- Modify: `assets/maps/route_1.json`
- Modify: `src/world.py`

- [ ] **Step 1: Add 2 trainers to Route 1 map data**

```json
"trainers": [
  {
    "id": "youngster_joey", "type": "youngster",
    "x": 20, "y": 25, "facing": "left", "sight_range": 3,
    "team": [{"species": 19, "level": 4}],
    "defeated_flag": "trainer_youngster_joey",
    "dialog_before": "Hey! You look like a Pokemon trainer!",
    "dialog_after": "You're pretty good..."
  },
  {
    "id": "bug_catcher_rick", "type": "bug_catcher",
    "x": 18, "y": 15, "facing": "down", "sight_range": 4,
    "team": [{"species": 10, "level": 3}, {"species": 13, "level": 3}],
    "defeated_flag": "trainer_bug_catcher_rick",
    "dialog_before": "My bug Pokemon are the best!",
    "dialog_after": "Aww, my bugs lost..."
  }
]
```

- [ ] **Step 2: Implement trainer sight + battle trigger in world.py**

When player walks within `sight_range` tiles in front of trainer (based on facing):
- If trainer not in `defeated_trainers` list:
  - Show "!" above trainer
  - Trainer walks toward player
  - Start trainer battle
- After defeat: add to `defeated_trainers`, trainer shows `dialog_after`

- [ ] **Step 3: Test trainer battles in Route 1**

Walk near trainers, verify:
- "!" appears
- Battle triggers
- After winning, trainer doesn't re-trigger
- Save/load preserves defeated state

- [ ] **Step 4: Commit**

```bash
git add assets/maps/route_1.json src/world.py
git commit -m "feat: Add 2 trainers to Route 1 with sight-range battles"
```

---

## Chunk 5: Final Integration + Polish

### Task 10: Map Schema Migration

**Files:**
- Modify: `src/map.py`
- Modify: `assets/maps/pallet_town.json`
- Modify: `src/world.py`

- [ ] **Step 1: Move NPC data from world.py to map JSON**

Currently NPCs are hardcoded in `world.py`. Move them to the JSON map files under the `"npcs"` key. Update `world.py` to load NPCs from map data instead of hardcoding.

- [ ] **Step 2: Remove create_sample_maps() from map.py**

Ensure all maps load from JSON files in `assets/maps/`. Delete the 200+ line `create_sample_maps()` function. If pallet_town.json or route_1.json are incomplete, complete them first.

- [ ] **Step 3: Run all tests**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add src/map.py src/world.py assets/maps/
git commit -m "refactor: Load all maps from JSON, remove create_sample_maps()"
```

### Task 11: End-to-End Playtest

- [ ] **Step 1: Full playthrough test**

Start new game → select starter → explore Pallet Town → walk to Route 1 → battle 2 trainers → encounter wild Pidgey/Rattata → walk to Viridian City → heal at Pokemon Center → buy items at shop → save game → quit → continue from save → verify position/team/items restored.

- [ ] **Step 2: Edge case testing**

- White-out: let all Pokemon faint in battle → verify teleport to Pokemon Center
- Save corruption: manually corrupt save JSON → verify graceful fallback
- Party full: (for future Phase 2 — just verify 6 Pokemon limit exists)

- [ ] **Step 3: Run full test suite**

```bash
cd /home/ubuntu/바탕화면/workspace/poketmon_game && python -m pytest tests/ -v
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: Complete Phase 1 — save system, UI refactor, Viridian City, trainers"
```

---

## Summary

| Task | Description | Est. Time |
|------|------------|-----------|
| 1 | Save/Load core | 15 min |
| 2 | Save integration with game loop | 20 min |
| 3 | UI split into package | 30 min |
| 4 | Fix encounter tables | 10 min |
| 5 | New species data (4 Pokemon) | 15 min |
| 6 | White-out flow | 15 min |
| 7 | Shop system | 15 min |
| 8 | Viridian City map + healing + shop | 30 min |
| 9 | Route 1 trainers | 20 min |
| 10 | Map schema migration | 25 min |
| 11 | End-to-end playtest | 15 min |
| **Total** | | **~3.5 hrs** |
