import sqlite3

from dungeon import convert_string_to_layout, DATABASE_PATH, DungeonTile

def get_unique_tiles() -> set[DungeonTile]:
    """Get all tiles from the tilemap being used in practice (USED_DUNGEON_TILES)"""

    tiles: set[DungeonTile] = set()

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dungeons")

        for _, layout in cursor:
            dungeon = convert_string_to_layout(layout)

            for y in range(15):
                for x in range(15):
                    tiles.add(dungeon[y][x])

    return tiles

def main() -> None:
    """Traverse each dungeon to get the minimum, maximum, and average discovery length"""

if __name__ == "__main__":
    main()
