from ctypes import byref, c_uint32, sizeof, windll
from ctypes.wintypes import DWORD, HANDLE, HWND, LPCVOID
import json
import os
import time

# In order to run the script and to begin collecting dungeon layout screenshots follow these steps:
# 1. Open PCSX2 2.0 with Dark Cloud.
# 2. Have a state in the slot just after accepting to enter the floor, but before dungeon generation.
# 3. Have a breakpoint set at 0x001CB6F4 (`paddub a0, zero, zero`).
# 4. Use vmmap to determine the BASE_ADDRESS for the Emotion Engine memory in Windows

STARTING_SEED = 0x00000000

APPLICATION_WINDOW_TITLE = "Dark Cloud"
BASE_ADDRESS = 0x7FF810000000 # Use vmmap to determine this address!

def get_handle_window() -> HWND:
    """Get the handle of an already opened PCSX2 running the game"""

    return windll.user32.FindWindowW(None, APPLICATION_WINDOW_TITLE)

def get_handle_process(handle: HWND) -> HANDLE:
    """Get the handle of process associated with the window"""

    PROCESS_ALL_ACCESS = 0x000F0000 | 0x00100000 | 0xFFFF

    pid = DWORD()
    windll.user32.GetWindowThreadProcessId(handle, byref(pid))

    return windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

def read_memory(handle: HANDLE, address: int) -> int:
    """Read from the game's memory at the specific address"""

    packet = c_uint32()
    windll.kernel32.ReadProcessMemory(handle, LPCVOID(BASE_ADDRESS + address), byref(packet), sizeof(packet), None)

    return packet.value

def write_memory(handle: HANDLE, address: int, value: int) -> None:
    """Write to the game's memory at the specific address"""

    packet = c_uint32(value)
    windll.kernel32.WriteProcessMemory(handle, LPCVOID(BASE_ADDRESS + address), byref(packet), sizeof(packet), None)

def load_state(handle: HWND) -> None:
    """Load the starting state of the script"""

    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101

    VK_F3 = 0x72

    windll.user32.SendMessageW(handle, WM_KEYDOWN, VK_F3, 0)
    windll.user32.SendMessageW(handle, WM_KEYUP, VK_F3, 0)

def unpause(handle: HWND) -> None:
    """Unpause from a breakpoint in PCSX2"""

    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101

    VK_SPACE = 0x20

    windll.user32.SendMessageW(handle, WM_KEYDOWN, VK_SPACE, 0)
    windll.user32.SendMessageW(handle, WM_KEYUP, VK_SPACE, 0)

def screenshot(handle: HWND) -> None:
    """Press the hotkey to screenshot in PCSX2"""

    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101

    VK_F8 = 0x77

    windll.user32.SendMessageW(handle, WM_KEYDOWN, VK_F8, 0)
    windll.user32.SendMessageW(handle, WM_KEYUP, VK_F8, 0)

def get_seed(handle: HANDLE) -> int:
    """Get the seed after the dungeon generation"""

    ADDRESS_SEED = 0x0024FB58

    return read_memory(handle, ADDRESS_SEED)

def set_seed(handle: HANDLE, seed: int) -> None:
    """Set the seed for dungeon generation"""

    ADDRESS_SEED = 0x0024FB58

    write_memory(handle, ADDRESS_SEED, seed)

def get_map(handle: HANDLE) -> list[list[tuple[int, int]]]:
    """Get the map via memory"""

    def get_tile_id(tile: int, rotation: int) -> int:
        """Convert the tile ID from memory to our own tile ID"""

        if tile == 0x1F: # The exit has a rotation... it always is rotated the same way
            return 0x21

        tiles_to_ids = {
            0x00: 0x00, 0x01: 0x02, 0x02: 0x06, 0x03: 0x07, 0x05: 0x0B, 0x06: 0x0C, 0x07: 0x0D, 0x08: 0x0E,
            0x09: 0x0F, 0x0A: 0x10, 0x0B: 0x11, 0x0C: 0x12, 0x0D: 0x13, 0x0E: 0x14, 0x0F: 0x15, 0x10: 0x16,
            0x11: 0x17, 0x12: 0x18, 0x13: 0x19, 0x14: 0x1A, 0x15: 0x1B, 0x16: 0x1C, 0x17: 0x1D, 0x1A: 0x1E,
            0x1B: 0x1F, 0x1E: 0x20, 0x20: 0x22, 0x24: 0x23, 0x25: 0x24, 0x26: 0x25, 0x27: 0x26, 0x28: 0x27,
            0x2D: 0x28, 0x2E: 0x29
        }

        return tiles_to_ids[tile] + rotation if tile in tiles_to_ids else 0x2F

    ADDRESS_MAP = 0x01DCE830

    MAP_WIDTH = 15
    MAP_HEIGHT = 15
    TILE_STRUCT_SIZE = 0x10

    # The minimap is a 20x20 grid where each tile is a 16 byte structure. The first 4 bytes determines the id of the
    # tile being used. The second 4 bytes are used for rotating the tile. By checking all of the dungeons, only 43
    # unique tiles from the tileset are being used.
    return [
        [
            get_tile_id(read_memory(handle, ADDRESS_MAP + x + y) & 0x3F, read_memory(handle, ADDRESS_MAP + x + y + 4))
            for x in range(0, MAP_WIDTH*TILE_STRUCT_SIZE, TILE_STRUCT_SIZE)
        ] for y in range(0, MAP_HEIGHT*20*TILE_STRUCT_SIZE, 20*TILE_STRUCT_SIZE)
    ]

def stub_map(handle: HANDLE) -> None:
    """stub the minimap function to draw the entire thing"""

    ADDRESS_INSTRUCTION_1 = 0x001C323C
    ADDRESS_INSTRUCTION_2 = 0x001C32F8

    write_memory(handle, ADDRESS_INSTRUCTION_1, 0)
    write_memory(handle, ADDRESS_INSTRUCTION_2, 0)

def get_dungeon_data(hWnd: HWND, hProcess: HANDLE) -> None:
    """Collect the 20x20 grid from the generated dungeon"""

    path_to_maps = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/maps.json")

    with open(path_to_maps, "r") as f:
        maps = json.load(f)

    for i in range(STARTING_SEED, (2**31 - 1) // 100000 + 1):
        load_state(hWnd)

        time.sleep(3) # Wait for the breakpoint in CDungeonMap::buildRandomMap (After the srand call!)
        set_seed(hProcess, i)
        unpause(hWnd)

        time.sleep(0.1) # Wait for the 2nd call of that breakpoint
        unpause(hWnd)

        time.sleep(0.1)
        maps[f"{i:08X}"] = get_map(hProcess)

        #TODO: JSON is slow, some other option might be better
        with open(path_to_maps, "w") as f:
            json.dump(maps, f)

        print(f"[{time.time():.02f}] {i:08X}")

def get_dungeon_screenshots(hWnd: HWND, hProcess: HANDLE) -> None:
    """Collect screenshots of generated dungeons"""

    for i in range(STARTING_SEED, (2**31 - 1) // 100000 + 1):
        load_state(hWnd)

        time.sleep(3) # Wait for the breakpoint in CDungeonMap::buildRandomMap (After the srand call!)
        set_seed(hProcess, i)
        stub_map(hProcess)
        unpause(hWnd)

        time.sleep(0.1) # Wait for the 2nd call of that breakpoint
        unpause(hWnd)

        time.sleep(8) # Wait for the dungeon map to show
        screenshot(hWnd)

        print(f"[{time.time():.02f}] {i:08X}")

def main() -> None:
    """Open PCSX2 and start generating dungeons"""

    hWnd = get_handle_window()
    hProcess = get_handle_process(hWnd)

    get_dungeon_data(hWnd, hProcess)
    #get_dungeon_screenshots(hWnd, hProcess)

if __name__ == "__main__":
    main()
