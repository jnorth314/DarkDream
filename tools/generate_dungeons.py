import time
from typing import Callable

import win32con

from dungeon import convert_layout_to_string, create_database, create_dungeon_entry, DungeonLayout, DungeonTile
from libpcsx2 import PCSX2

# In order to run the script to begin collecting Dungeon layouts, follow these steps:
# 1. Open PCSX2 2.0 with Dark Cloud.
# 2. Have a state in the slot just after accepting enter the floor, but before dungeon generation.
#    (Just use the breakpoint on the following step and save the state on the first execution)
# 3. Set a breakpoint at 0x001CB6F4 ('paddub a0, zero, zero')

def load_state(pcsx2: PCSX2) -> None:
    """Load the state at the start of the Dungeon generating"""

    pcsx2._press_key(win32con.VK_F3)
    time.sleep(0.3)

def write_seed(pcsx2: PCSX2, seed: int) -> None:
    """Write the seed to the appropriate address"""

    SEED_ADDRESS = 0x0024FB58

    pcsx2.write_u32(SEED_ADDRESS, seed)

def wait_for_generation(pcsx2: PCSX2) -> None:
    """Advance through the breakpoints to generate the dungeon"""

    pcsx2._press_key(win32con.VK_SPACE)
    time.sleep(0.1)
    pcsx2._press_key(win32con.VK_SPACE)

def read_dungeon_map(pcsx2: PCSX2) -> DungeonLayout:
    """Return the contents of the dungeon map"""

    DUNGEON_MAP_ADDRESS = 0x01DCE830

    get_idx: Callable[[int, int], int] = lambda x, y : (20*y + x) << 4

    return [
        [DungeonTile(
            pcsx2.read_u32(DUNGEON_MAP_ADDRESS + get_idx(x, y)),
            pcsx2.read_u32(DUNGEON_MAP_ADDRESS + get_idx(x, y) + 4)
         ) for x in range(15)]
        for y in range(15)
    ]

def main() -> None:
    """A script designed to create a database of all 21475 Dark Cloud dungeon layouts"""

    pcsx2 = PCSX2("Dark Cloud")

    create_database()

    for i in range(21475):
        load_state(pcsx2)
        write_seed(pcsx2, i)
        wait_for_generation(pcsx2)

        layout = read_dungeon_map(pcsx2)
        create_dungeon_entry(i, convert_layout_to_string(layout))

if __name__ == "__main__":
    main()
