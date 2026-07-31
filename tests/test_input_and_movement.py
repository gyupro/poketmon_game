"""
Test input handling across state changes and continuous grid movement.
"""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.player import Player


class TestContinuousMovement(unittest.TestCase):
    """Holding a direction should scroll at a steady rate, without stalls."""

    def setUp(self):
        self.player = Player("Test", 10, 10)

    def test_step_overshoot_carries_into_next_step(self):
        """The fraction of a step past the tile edge isn't thrown away."""
        # 0.1s at 8 tiles/sec = 0.8 of a step; two updates overshoot by 0.6
        self.player.start_move("right")
        self.player.update(0.1)
        self.player.update(0.1)

        self.assertFalse(self.player.is_moving)
        self.assertAlmostEqual(self.player.move_carry, 0.6, places=5)

        # The next step starts from that overshoot rather than from zero
        self.player.start_move("right")
        self.assertAlmostEqual(self.player.move_progress, 0.6, places=5)
        self.assertEqual(self.player.move_carry, 0.0)

    def test_no_cooldown_between_steps(self):
        """A finished step doesn't block the next one."""
        self.player.start_move("right")
        self.player.update(0.2)
        self.assertFalse(self.player.is_moving)
        self.assertTrue(self.player.start_move("right"))

    def test_held_direction_keeps_full_speed(self):
        """Holding a direction covers the full distance, with no stalled frames.

        Snapping to the tile grid can shift a fraction of a frame's movement
        into the next frame, but the tile seam must not cost any time: before
        the carry was added, every boundary dropped a frame plus a 0.02s
        cooldown, which is what made walking look like it was hitching.
        """
        dt = 1 / 60
        frames = 60
        speed_px = Player.MOVE_SPEED * Player.TILE_SIZE * dt  # per-frame distance
        start = self.player.pixel_x

        positions = []
        for _ in range(frames):
            # Mirrors Game.update_world: input, update, then input again so a
            # step finishing inside update() rolls straight into the next one
            if not self.player.is_moving:
                self.player.start_move("right")
            self.player.update(dt)
            if not self.player.is_moving:
                self.player.start_move("right")
            positions.append(self.player.pixel_x)

        # No time lost overall (one step of slack for the in-progress tile)
        travelled = self.player.pixel_x - start
        self.assertGreater(travelled, speed_px * frames - Player.TILE_SIZE)

        # And no frame pair where the player is standing still
        deltas = [b - a for a, b in zip(positions, positions[1:])]
        for i in range(len(deltas) - 1):
            pair = deltas[i] + deltas[i + 1]
            self.assertGreater(pair, speed_px,
                               f"movement stalled at frame {i}: {deltas}")


class TestHeldKeyTracking(unittest.TestCase):
    """Key state must stay accurate even when the UI swallows events."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def setUp(self):
        from src.game import Game

        self.game = Game()
        self.game.create_new_game()
        self.game.select_starter(1)
        self.game.world.current_map_id = "route_1"
        self.game.world.current_map = self.game.world.maps["route_1"]

    def _pump(self, *events):
        pygame.event.clear()
        for event_type, key in events:
            pygame.event.post(pygame.event.Event(event_type, key=key))
        self.game.handle_events()

    def test_keyup_recorded_while_ui_blocks_input(self):
        """The VS screen blocks input, but a release must still be recorded."""
        self._pump((pygame.KEYDOWN, pygame.K_RIGHT))
        self.assertTrue(self.game.keys_pressed[pygame.K_RIGHT])

        self.game.trigger_wild_encounter()
        self.game.update(1 / 60)
        self.assertTrue(
            self.game.ui._battle_ui.battle_animation_manager.has_vs_screen())

        self._pump((pygame.KEYUP, pygame.K_RIGHT))
        self.assertFalse(self.game.keys_pressed[pygame.K_RIGHT])

    def test_player_does_not_walk_after_battle(self):
        """A direction held into a battle doesn't drive the player afterwards."""
        self._pump((pygame.KEYDOWN, pygame.K_RIGHT))
        self.game.trigger_wild_encounter()
        self.game.update(1 / 60)
        self._pump((pygame.KEYUP, pygame.K_RIGHT))

        self.game.current_battle.is_over = True
        self.game.end_battle()

        start = self.game.player.get_grid_position()
        for _ in range(60):
            self.game.update(1 / 60)
        self.assertEqual(start, self.game.player.get_grid_position())


if __name__ == "__main__":
    unittest.main()
