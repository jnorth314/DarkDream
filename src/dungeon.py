from dataclasses import dataclass
from functools import cache
import os
import re
import sqlite3
import sys
from typing import Callable

import cv2

IS_FROZEN = hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS") # For PyInstaller
BASE_DIRECTORY = sys._MEIPASS if IS_FROZEN else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

DATABASE_PATH = os.path.join(BASE_DIRECTORY, "res/DUNGEONS.db")
TILES_PATH = os.path.join(BASE_DIRECTORY, "res/tiles.png")

@dataclass(unsafe_hash=True)
class DungeonTile:
    id_: int
    rotation: int

type Dungeon = list[list[DungeonTile]]

USED_DUNGEON_TILES = [ # Precomputed from DUNGEONS.db
    DungeonTile(0xFFFFFFFF, 0),
    DungeonTile(0x00, 0), DungeonTile(0x00, 1), DungeonTile(0x01, 0), DungeonTile(0x01, 1),
    DungeonTile(0x01, 2), DungeonTile(0x01, 3), DungeonTile(0x02, 0), DungeonTile(0x03, 0),
    DungeonTile(0x03, 1), DungeonTile(0x03, 2), DungeonTile(0x03, 3), DungeonTile(0x05, 0),
    DungeonTile(0x06, 0), DungeonTile(0x07, 0), DungeonTile(0x08, 0), DungeonTile(0x09, 0),
    DungeonTile(0x0A, 0), DungeonTile(0x0B, 0), DungeonTile(0x0C, 0), DungeonTile(0x0D, 0),
    DungeonTile(0x0E, 0), DungeonTile(0x0F, 0), DungeonTile(0x10, 0), DungeonTile(0x11, 0),
    DungeonTile(0x12, 0), DungeonTile(0x13, 0), DungeonTile(0x14, 0), DungeonTile(0x15, 0),
    DungeonTile(0x16, 0), DungeonTile(0x17, 0), DungeonTile(0x1A, 0), DungeonTile(0x1B, 0),
    DungeonTile(0x1E, 0), DungeonTile(0x1F, 2), DungeonTile(0x20, 0), DungeonTile(0x24, 0),
    DungeonTile(0x25, 0), DungeonTile(0x26, 0), DungeonTile(0x27, 0), DungeonTile(0x28, 0),
    DungeonTile(0x2D, 0), DungeonTile(0x2E, 0)
]

def get_hex_from_tile(tile: DungeonTile) -> str:
    """Convert the tile into a hex string"""

    if tile.id_ == 0xFFFFFFFF:
        tile_as_int = 0xFF
    else:
        tile_as_int = (tile.id_ << 2) + tile.rotation

    if tile_as_int > 0xFF:
        raise ValueError(f"Invalid Tile Data ({tile.id_}, {tile.rotation})")

    return f"{tile_as_int:02X}"

def get_tile_from_hex(tile: str) -> DungeonTile:
    """Convert the hex string into a tile"""

    tile_as_int = int(tile, 16)

    if tile_as_int == 0xFF:
        id_, rotation = 0xFFFFFFFF, 0
    else:
        id_, rotation = tile_as_int >> 2, tile_as_int & 0b11

    return DungeonTile(id_, rotation)

def convert_dungeon_to_string(dungeon: Dungeon) -> str:
    """Convert the dungeon into a hex string for storage"""

    return "".join(get_hex_from_tile(dungeon[y][x]) for y in range(15) for x in range(15))

def convert_dungeon_to_regex(dungeon: Dungeon) -> str:
    """Convert the dungeon into a regex string for matching"""

    WILDCARDS = {DungeonTile(0xFFFFFFFF, 0)}

    regex = ""
    consecutive_wildcards = 0

    for y in range(15):
        for x in range(15):
            if dungeon[y][x] in WILDCARDS:
                consecutive_wildcards += 1
            else:
                if consecutive_wildcards > 0:
                    regex += f"(..){{{consecutive_wildcards}}}"
                    consecutive_wildcards = 0

                regex += get_hex_from_tile(dungeon[y][x])

    if consecutive_wildcards > 0:
        regex += f"(..){{{consecutive_wildcards}}}"

    return regex

def convert_string_to_dungeon(dungeon: str) -> Dungeon:
    """Convert the hex string into a dungeon"""

    if len(dungeon) != (15*15) << 1:
        raise ValueError(f"Invalid Dungeon String Length ({len(dungeon)})")

    get_idx: Callable[[int, int], int] = lambda x, y : (15*y + x) << 1

    return [
        [get_tile_from_hex(dungeon[get_idx(x, y):get_idx(x, y) + 2]) for x in range(15)]
        for y in range(15)
    ]

def create_database() -> None:
    """Create the sqlite3 database to hold the dungeon layouts"""

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS dungeons (seed INTEGER PRIMARY KEY, layout TEXT)")
        connection.commit()

def create_dungeon_entry(seed: int, dungeon: str) -> None:
    """Create the entry in the database for the dungeon layout"""

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(f"INSERT OR REPLACE INTO dungeons VALUES ({seed}, {dungeon})")
        connection.commit()

def get_matching_dungeons(dungeon: Dungeon) -> list[str]:
    """Get a list of matching dungeon strings"""

    dungeons:  list[str] = []

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.create_function("REGEXP", 2, lambda pattern, string : re.search(pattern, string) is not None)

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM dungeons WHERE layout REGEXP \"{convert_dungeon_to_regex(dungeon)}\"")

        for _, layout in cursor:
            dungeons.append(layout)

    return dungeons

@cache
def get_tile_image(tile: DungeonTile) -> cv2.typing.MatLike:
    """Get the texture of the tile in the tile sheet"""

    if tile.id_ == 0xFFFFFFFF:
        x, y = 0, 0
    else:
        x, y = 16*tile.rotation, 16*(tile.id_ + 1)

    return cv2.imread(TILES_PATH)[y:y + 16, x:x + 16]

HASHABLE_TILES = [ # Ignoring specific tiles during image recognition
    DungeonTile(0x00, 0), DungeonTile(0x00, 1), DungeonTile(0x02, 0), DungeonTile(0x03, 0),
    DungeonTile(0x03, 1), DungeonTile(0x03, 2), DungeonTile(0x03, 3), DungeonTile(0x05, 0),
    DungeonTile(0x06, 0), DungeonTile(0x07, 0), DungeonTile(0x08, 0), DungeonTile(0x09, 0),
    DungeonTile(0x0A, 0), DungeonTile(0x0B, 0), DungeonTile(0x0C, 0), DungeonTile(0x0D, 0),
    DungeonTile(0x0E, 0), DungeonTile(0x0F, 0), DungeonTile(0x10, 0), DungeonTile(0x12, 0),
    DungeonTile(0x13, 0), DungeonTile(0x14, 0), DungeonTile(0x15, 0), DungeonTile(0x16, 0),
    DungeonTile(0x17, 0), DungeonTile(0x1A, 0), DungeonTile(0x1B, 0), DungeonTile(0x1E, 0),
    DungeonTile(0x1F, 2), DungeonTile(0x20, 0), DungeonTile(0x24, 0), DungeonTile(0x25, 0),
    DungeonTile(0x26, 0), DungeonTile(0x27, 0), DungeonTile(0x28, 0)
]

SCORE_THRESHOLD = 0.90

def get_image_phash(img: cv2.typing.MatLike) -> cv2.typing.MatLike:
    """Calculate the phash of a given image"""

    return cv2.img_hash.pHash(cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA))

@cache
def get_tile_phash(tile: DungeonTile) -> cv2.typing.MatLike:
    """Calculate the phash of a given tile"""

    return get_image_phash(get_tile_image(tile))

def get_dungeon_from_image(img: cv2.typing.MatLike) -> Dungeon:
    """Get the best fit for every tile in the provided image"""

    def get_best_fit_tile(img: cv2.typing.MatLike) -> DungeonTile:
        """Compare the phash amongst all tiles to find which one is the highest score, while meeting a threshold"""

        module = cv2.img_hash.PHash.create()
        phash = get_image_phash(img)

        get_similarity: Callable[[DungeonTile], float] = (
            lambda tile: 1.0 - module.compare(phash, get_tile_phash(tile))/64.0
        )

        tile = max(HASHABLE_TILES, key=get_similarity)

        if get_similarity(tile) < SCORE_THRESHOLD:
            return DungeonTile(0xFFFFFFFF, 0)

        return tile

    img = cv2.resize(img, (16*15, 16*15))

    return [
        [get_best_fit_tile(img[16*y:16*y + 16, 16*x:16*x + 16]) for x in range(15)]
         for y in range(15)
    ]
