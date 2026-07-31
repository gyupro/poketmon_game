"""
Test that every map is navigable: exits open, doors real, NPCs on solid ground.

These are the failures a player hits as "I can't get out of Route 1" or "this
door doesn't do anything", so they are checked on the real generated maps
rather than on fixtures.
"""

import json
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.map import TileType, create_sample_maps, flood_fill, validate_maps
from src.world import World


MAPS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "maps"
)


class TestMapIntegrity(unittest.TestCase):
    """Structural checks over every generated map."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 800))
        cls.maps = create_sample_maps()

    def test_no_validation_problems(self):
        """The builder's own checks pass -- warps, doors, signs, reachability."""
        self.assertEqual(validate_maps(self.maps), [])

    def test_every_map_is_fully_walkable(self):
        """No walkable ground is fenced off where the player can never reach it."""
        for map_id, m in self.maps.items():
            with self.subTest(map=map_id):
                start = (m.warps[0].x, m.warps[0].y)
                reachable = flood_fill(m, start)
                stranded = [
                    (x, y)
                    for y in range(m.height)
                    for x in range(m.width)
                    if m.is_walkable(x, y) and (x, y) not in reachable
                ]
                self.assertEqual(stranded, [], f"{map_id} has unreachable ground")

    def test_gates_are_two_way(self):
        """Every exit leads somewhere that leads back, and lands on open ground."""
        for map_id, m in self.maps.items():
            for warp in m.warps:
                with self.subTest(map=map_id, warp=(warp.x, warp.y)):
                    target = self.maps[warp.target_map]
                    self.assertTrue(m.is_walkable(warp.x, warp.y))
                    self.assertTrue(target.is_walkable(warp.target_x, warp.target_y))
                    # Landing on the return warp would bounce the player back
                    self.assertIsNone(
                        target.get_warp_at(warp.target_x, warp.target_y))
                    self.assertTrue(
                        any(back.target_map == map_id for back in target.warps))

    def test_every_door_opens_onto_a_real_room(self):
        for map_id, m in self.maps.items():
            for y in range(m.height):
                for x in range(m.width):
                    tile = m.tiles[y][x]
                    if not tile or tile.type != TileType.DOOR:
                        continue
                    with self.subTest(map=map_id, door=(x, y)):
                        warp = m.get_warp_at(x, y)
                        self.assertIsNotNone(warp, "door with nothing behind it")
                        self.assertIn(warp.target_map, self.maps)


class TestMapMetadata(unittest.TestCase):
    """The JSON files must describe the maps they are actually loaded against."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 800))
        cls.maps = create_sample_maps()
        cls.world = World()

    def test_json_dimensions_match_generated_maps(self):
        for map_id, m in self.maps.items():
            path = os.path.join(MAPS_DIR, f"{map_id}.json")
            if not os.path.exists(path):
                continue
            with self.subTest(map=map_id):
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                self.assertEqual((data["width"], data["height"]), (m.width, m.height))

    def test_npcs_stand_on_walkable_ground(self):
        """An NPC inside a tree or a wall can never be spoken to."""
        for map_id, npcs in self.world.npcs.items():
            m = self.maps[map_id]
            for npc in npcs:
                with self.subTest(map=map_id, npc=npc.name):
                    self.assertTrue(
                        m.is_walkable(npc.x, npc.y),
                        f"{npc.name} at ({npc.x},{npc.y}) is stuck in scenery")

    def test_npcs_can_be_reached(self):
        """Every NPC has an adjacent tile the player can stand on to talk."""
        for map_id, npcs in self.world.npcs.items():
            m = self.maps[map_id]
            reachable = flood_fill(m, (m.warps[0].x, m.warps[0].y))
            for npc in npcs:
                with self.subTest(map=map_id, npc=npc.name):
                    self.assertTrue(
                        any((npc.x + dx, npc.y + dy) in reachable
                            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))),
                        f"{npc.name} cannot be approached")

    def test_tall_grass_has_an_encounter_table(self):
        """Grass that never spawns anything is a broken promise to the player."""
        for map_id, m in self.maps.items():
            has_grass = any(
                m.tiles[y][x] and m.tiles[y][x].type == TileType.TALL_GRASS
                for y in range(m.height) for x in range(m.width)
            )
            if has_grass:
                with self.subTest(map=map_id):
                    self.assertIn(map_id, self.world.encounter_system.encounter_tables)


if __name__ == "__main__":
    unittest.main()
