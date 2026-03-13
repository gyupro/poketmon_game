"""
Tests for the save/load system.
"""

import os
import json
import tempfile
import shutil
import pytest

from src.save_system import SaveData, SaveSystem


@pytest.fixture
def tmp_save_dir(tmp_path):
    """Provide a temporary directory for save files."""
    save_dir = tmp_path / "saves"
    save_dir.mkdir()
    return str(save_dir)


@pytest.fixture
def save_system(tmp_save_dir):
    """Provide a SaveSystem using a temporary directory."""
    return SaveSystem(save_dir=tmp_save_dir)


@pytest.fixture
def sample_data():
    """Provide a sample SaveData for testing."""
    return SaveData.new_game(name="Ash", starter_id=1)


def test_save_creates_file(save_system, sample_data, tmp_save_dir):
    """Saving creates a .json file in the save directory."""
    save_system.save(slot=1, data=sample_data)
    expected_path = os.path.join(tmp_save_dir, "slot_1.json")
    assert os.path.exists(expected_path)


def test_load_returns_saved_data(save_system, sample_data):
    """Loading a previously saved slot returns equivalent SaveData."""
    save_system.save(slot=1, data=sample_data)
    loaded = save_system.load(slot=1)
    assert loaded is not None
    assert loaded.player_name == "Ash"
    assert loaded.money == 3000
    assert len(loaded.team) == 1
    assert loaded.team[0]["species_id"] == 1
    assert loaded.bag["potion"] == 5
    assert loaded.bag["pokeball"] == 5


def test_save_has_version(save_system, sample_data, tmp_save_dir):
    """Saved file contains a version field."""
    save_system.save(slot=1, data=sample_data)
    path = os.path.join(tmp_save_dir, "slot_1.json")
    with open(path, "r") as f:
        raw = json.load(f)
    assert "version" in raw
    assert raw["version"] == 1


def test_load_nonexistent_returns_none(save_system):
    """Loading a slot that has no save file returns None."""
    result = save_system.load(slot=99)
    assert result is None


def test_slot_has_save(save_system, sample_data):
    """has_save returns True only for slots with an existing save file."""
    assert save_system.has_save(slot=1) is False
    save_system.save(slot=1, data=sample_data)
    assert save_system.has_save(slot=1) is True


def test_save_validation_clamps_hp(save_system):
    """Loading a save with HP exceeding max_hp gets clamped."""
    data = SaveData.new_game(name="Misty", starter_id=7)
    # Corrupt the HP to exceed max
    data.team[0]["current_hp"] = 9999
    save_system.save(slot=1, data=data)
    loaded = save_system.load(slot=1)
    assert loaded is not None
    assert loaded.team[0]["current_hp"] <= loaded.team[0]["max_hp"]


def test_atomic_write_no_partial(save_system, sample_data, tmp_save_dir):
    """After a successful save, no .tmp file remains in the directory."""
    save_system.save(slot=1, data=sample_data)
    tmp_files = [f for f in os.listdir(tmp_save_dir) if f.endswith(".tmp")]
    assert len(tmp_files) == 0
    # The final file must exist
    assert os.path.exists(os.path.join(tmp_save_dir, "slot_1.json"))
