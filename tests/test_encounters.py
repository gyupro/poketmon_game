"""
Test suite for the Pokemon encounter system
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.encounters import EncounterSystem, TimeOfDay
from src.map import Map, Tile, TileType
from src.world import World
from src.player import Player


class TestEncounterSystem(unittest.TestCase):
    """Test encounter system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encounter_system = EncounterSystem()
        
    def test_base_encounter_rates(self):
        """Test that base encounter rates are reasonable."""
        for area, table in self.encounter_system.encounter_tables.items():
            self.assertGreaterEqual(table.base_encounter_rate, 5)
            self.assertLessEqual(table.base_encounter_rate, 25)
            print(f"{area}: {table.base_encounter_rate}% base rate")
    
    def test_should_encounter_calculation(self):
        """Test encounter rate calculation with various factors."""
        # Test with Route 1
        area = "route_1"
        
        # Test base rate (should be around 12%)
        encounters = 0
        trials = 10000
        for _ in range(trials):
            if self.encounter_system.should_encounter(area, steps_in_grass=1):
                encounters += 1
        
        rate = (encounters / trials) * 100
        print(f"Base encounter rate for {area}: {rate:.1f}%")
        self.assertGreater(rate, 10)  # Should be at least 10%
        self.assertLess(rate, 20)     # Should be less than 20%
        
    def test_step_bonus(self):
        """Test that consecutive steps increase encounter rate."""
        area = "route_1"
        
        # Test with increasing steps
        rates = []
        for steps in [1, 5, 10, 15]:
            encounters = 0
            trials = 1000
            for _ in range(trials):
                if self.encounter_system.should_encounter(area, steps_in_grass=steps):
                    encounters += 1
            rate = (encounters / trials) * 100
            rates.append(rate)
            print(f"Encounter rate with {steps} steps: {rate:.1f}%")
        
        # Rates should increase with more steps
        for i in range(1, len(rates)):
            self.assertGreaterEqual(rates[i], rates[i-1])
    
    def test_time_of_day_modifier(self):
        """Test time of day affects encounter rates."""
        area = "route_1"
        
        time_rates = {}
        for time in [TimeOfDay.DAY, TimeOfDay.MORNING, TimeOfDay.NIGHT]:
            with patch.object(self.encounter_system, 'get_time_of_day', return_value=time):
                encounters = 0
                trials = 1000
                for _ in range(trials):
                    if self.encounter_system.should_encounter(area, steps_in_grass=5):
                        encounters += 1
                rate = (encounters / trials) * 100
                time_rates[time] = rate
                print(f"Encounter rate during {time.value}: {rate:.1f}%")
        
        # Night should have highest rate, then morning, then day
        self.assertGreater(time_rates[TimeOfDay.NIGHT], time_rates[TimeOfDay.DAY])
        self.assertGreater(time_rates[TimeOfDay.MORNING], time_rates[TimeOfDay.DAY])


class TestGrassTileDetection(unittest.TestCase):
    """Test grass tile detection."""
    
    def setUp(self):
        """Set up test map."""
        self.map = Map("test_map", 10, 10, "Test Map")
        
    def test_tile_wild_encounter_flag(self):
        """Test that grass tiles have wild_encounter flag."""
        # Create different tile types
        grass_tile = Tile(TileType.TALL_GRASS, 0, 0)
        ground_tile = Tile(TileType.GRASS, 1, 0)
        water_tile = Tile(TileType.WATER, 2, 0)
        
        # Only grass should have wild encounters
        self.assertTrue(grass_tile.wild_encounter)
        self.assertFalse(ground_tile.wild_encounter)
        self.assertFalse(water_tile.wild_encounter)
    
    def test_map_check_wild_encounter(self):
        """Test map's check_wild_encounter method."""
        # Add grass tiles to map
        for x in range(3):
            for y in range(3):
                self.map.set_tile(x, y, TileType.TALL_GRASS)
        
        # Add non-grass tiles
        self.map.set_tile(5, 5, TileType.GRASS)
        self.map.set_tile(6, 6, TileType.WATER)
        
        # Check grass tiles
        for x in range(3):
            for y in range(3):
                self.assertTrue(self.map.check_wild_encounter(x, y), 
                              f"Tile at ({x}, {y}) should trigger encounters")
        
        # Check non-grass tiles
        self.assertFalse(self.map.check_wild_encounter(5, 5))
        self.assertFalse(self.map.check_wild_encounter(6, 6))
        
        # Check out of bounds
        self.assertFalse(self.map.check_wild_encounter(-1, 0))
        self.assertFalse(self.map.check_wild_encounter(100, 100))


class TestWorldEncounterIntegration(unittest.TestCase):
    """Test world encounter integration."""
    
    def setUp(self):
        """Set up test world."""
        # Mock pygame screen
        self.screen_mock = MagicMock()
        self.screen_mock.get_width.return_value = 800
        self.screen_mock.get_height.return_value = 600
        
        with patch('pygame.display.set_mode', return_value=self.screen_mock):
            self.world = World()
            self.player = Player("Test", 5, 5)
    
    def test_encounter_trigger_in_grass(self):
        """Test that encounters can trigger when walking in grass."""
        # Change to a map with encounters (Route 1)
        self.world.current_map_id = "route_1"
        
        # Place grass tiles
        for x in range(3, 8):
            for y in range(3, 8):
                self.world.current_map.set_tile(x, y, TileType.TALL_GRASS)
        
        # Move player to grass
        self.player.grid_x = 5
        self.player.grid_y = 5
        self.player.pixel_x = 5 * 32
        self.player.pixel_y = 5 * 32
        self.player.is_moving = False
        
        # Track encounter triggers
        encounter_triggered = False
        attempts = 0
        max_attempts = 100
        
        # Simulate multiple steps in grass
        while not encounter_triggered and attempts < max_attempts:
            # Simulate player moving to a new tile
            # Move player in a small pattern to simulate walking
            new_x = 5 + (attempts % 3)
            new_y = 5 + ((attempts // 3) % 3)
            self.player.grid_x = new_x
            self.player.grid_y = new_y
            self.player.pixel_x = new_x * 32
            self.player.pixel_y = new_y * 32
            
            # Update world
            result = self.world.update(0.016, self.player)  # 60 FPS
            
            if result == "wild_encounter":
                encounter_triggered = True
                print(f"Encounter triggered after {attempts + 1} steps")
            
            attempts += 1
        
        # Should trigger within reasonable number of steps
        self.assertTrue(encounter_triggered, 
                       f"No encounter triggered after {max_attempts} steps in grass")
        self.assertLess(attempts, 50, 
                       "Encounter rate seems too low - took too many steps")


class TestEncounterDebug(unittest.TestCase):
    """Debug tests to identify encounter issues."""
    
    def test_encounter_chain(self):
        """Test the complete encounter chain from movement to trigger."""
        print("\n=== Testing Complete Encounter Chain ===")
        
        # 1. Test tile creation
        grass_tile = Tile(TileType.TALL_GRASS, 5, 5)
        print(f"1. Grass tile wild_encounter flag: {grass_tile.wild_encounter}")
        self.assertTrue(grass_tile.wild_encounter)
        
        # 2. Test map tile check
        map_obj = Map("test", 10, 10)
        map_obj.set_tile(5, 5, TileType.TALL_GRASS)
        has_encounter = map_obj.check_wild_encounter(5, 5)
        print(f"2. Map check_wild_encounter(5, 5): {has_encounter}")
        self.assertTrue(has_encounter)
        
        # 3. Test encounter system
        enc_system = EncounterSystem()
        
        # Test multiple attempts
        print("\n3. Testing encounter rates:")
        for steps in [1, 5, 10]:
            successes = sum(1 for _ in range(100) 
                          if enc_system.should_encounter("route_1", steps))
            print(f"   Steps: {steps}, Triggers: {successes}/100")
        
        # 4. Test with different areas
        print("\n4. Testing different areas:")
        for area in ["route_1", "viridian_forest", "route_22"]:
            if area in enc_system.encounter_tables:
                base_rate = enc_system.encounter_tables[area].base_encounter_rate
                triggers = sum(1 for _ in range(100) 
                             if enc_system.should_encounter(area, 5))
                print(f"   {area}: base={base_rate}%, actual={triggers}%")


if __name__ == "__main__":
    unittest.main(verbosity=2)