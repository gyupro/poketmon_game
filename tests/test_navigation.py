"""
Test navigation and map transitions
"""

import unittest
from src.world import World
from src.player import Player
from src.map import Warp


class TestNavigation(unittest.TestCase):
    """Test map navigation and warp functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world = World()
        self.player = Player("Test", 20, 3)  # Start near Route 1 exit in Pallet Town
        
    def test_route1_transition_no_loop(self):
        """Test that going to Route 1 doesn't immediately send player back."""
        # Start in Pallet Town near the exit
        self.assertEqual(self.world.current_map_id, "pallet_town")
        self.player.grid_x = 20
        self.player.grid_y = 1  # One tile below the warp
        
        # Move up to the warp position
        self.player.grid_y = 0
        self.player.pixel_y = 0
        
        # Check for warps - should transport to Route 1
        self.world.check_warps(self.player)
        
        # Verify we're in Route 1
        self.assertEqual(self.world.current_map_id, "route_1")
        # Verify position (should be at y=38 after the fix)
        self.assertEqual(self.player.grid_y, 38)
        
        # Now move one step up (away from the return warp)
        self.player.grid_y = 37
        self.player.pixel_y = 37 * 32
        
        # Check warps again - should NOT transport back
        self.world.check_warps(self.player)
        self.assertEqual(self.world.current_map_id, "route_1")
        self.assertEqual(self.player.grid_y, 37)
        
    def test_route1_to_pallet_transition(self):
        """Test returning from Route 1 to Pallet Town."""
        # Start in Route 1
        self.world.change_map("route_1", 20, 38, self.player)
        self.assertEqual(self.world.current_map_id, "route_1")
        
        # Move to the return warp
        self.player.grid_y = 39
        self.player.pixel_y = 39 * 32
        
        # Check warps - should transport to Pallet Town
        self.world.check_warps(self.player)
        
        # Verify we're back in Pallet Town
        self.assertEqual(self.world.current_map_id, "pallet_town")
        self.assertEqual(self.player.grid_y, 1)
        
    def test_warp_positions_correct(self):
        """Test that warp positions are set up correctly."""
        pallet_town = self.world.maps["pallet_town"]
        route_1 = self.world.maps["route_1"]
        
        # Check Pallet Town exit warps
        pallet_warps = [w for w in pallet_town.warps if w.target_map == "route_1"]
        self.assertEqual(len(pallet_warps), 5)  # 5 tiles wide (18-22)
        for warp in pallet_warps:
            self.assertEqual(warp.y, 0)  # At the top edge
            self.assertEqual(warp.target_y, 38)  # Target is y=38 in Route 1
            self.assertIn(warp.x, range(18, 23))
            
        # Check Route 1 return warps
        route_warps = [w for w in route_1.warps if w.target_map == "pallet_town"]
        self.assertEqual(len(route_warps), 5)  # 5 tiles wide
        for warp in route_warps:
            self.assertEqual(warp.y, 39)  # At the bottom edge
            self.assertEqual(warp.target_y, 1)  # Target is y=1 in Pallet Town
            self.assertIn(warp.x, range(18, 23))
            
    def test_buffer_zone_exists(self):
        """Test that there's a buffer zone between warps."""
        # When arriving in Route 1 from Pallet Town
        self.world.change_map("route_1", 20, 38, self.player)
        
        # The arrival position (y=38) should not have a warp
        warp_at_arrival = self.world.current_map.get_warp_at(20, 38)
        self.assertIsNone(warp_at_arrival, "There should be no warp at the arrival position")
        
        # The warp back should be one tile away
        warp_back = self.world.current_map.get_warp_at(20, 39)
        self.assertIsNotNone(warp_back, "There should be a warp one tile south")
        

if __name__ == '__main__':
    unittest.main()