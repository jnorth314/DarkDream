import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import unittest
from unittest.mock import Mock, patch

from compare import get_tiles, get_maps, is_matching_dungeon

class TestScannerApp(unittest.TestCase):
    def test_get_tiles(self):
        self.assertEqual(len(get_tiles()), 8*6)

    def test_get_maps(self):
        self.assertEqual(len(get_maps()), 21475)

    def test_is_matching_dungeon(self):
        dungeon = [[-1 for _ in range(15)] for _ in range(15)]
        map_ = [[0 for _ in range(15)] for _ in range(15)]

        self.assertTrue(is_matching_dungeon(dungeon, map_))

        dungeon[0][0] = 0
        self.assertTrue(is_matching_dungeon(dungeon, map_))

        dungeon[0][1] = 1
        self.assertFalse(is_matching_dungeon(dungeon, map_))

if __name__ == "__main__":
    unittest.main()
