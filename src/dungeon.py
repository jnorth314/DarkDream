from dataclasses import astuple, dataclass
import os
import sqlite3
from typing import Callable

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/DUNGEONS.db")

@dataclass(unsafe_hash=True)
class DungeonTile:
    id_: int
    rotation: int

type Dungeon = list[list[DungeonTile]]

@dataclass
class DungeonEntry:
    seed: int
    layout: str

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
        cursor.execute(
            "INSERT OR REPLACE INTO dungeons VALUES (?, ?)",
            astuple(DungeonEntry(seed, dungeon))
        )
        connection.commit()

def get_matching_dungeons(dungeon: Dungeon) -> list[Dungeon]:
    """Get a list of matching dungeons"""

    #TODO: RegEx on sqlite3 query?

    dungeons:  list[Dungeon] = []
    wildcards = {DungeonTile(0xFFFFFFFF, 0)}

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dungeons")

        for _, layout in cursor:
            minimap = convert_string_to_dungeon(layout)

            if all(dungeon[y][x] in wildcards or dungeon[y][x] == minimap[y][x]
                   for x in range(15)
                   for y in range(15)):
                dungeons.append(minimap)

    return dungeons
