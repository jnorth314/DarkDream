import sqlite3

from dungeon import convert_string_to_layout, convert_string_to_treasure, DATABASE_PATH, DungeonTile

def get_unique_tiles() -> set[DungeonTile]:
    """Get all tiles from the tilemap being used in practice (USED_DUNGEON_TILES)"""

    tiles: set[DungeonTile] = set()

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dungeons")

        for _, layout, _ in cursor:
            dungeon = convert_string_to_layout(layout)

            for y in range(15):
                for x in range(15):
                    tiles.add(dungeon[y][x])

    return tiles

def get_unique_chest_items() -> set[int]:
    """Get all items that can be obtained from chests in a dungeon"""

    items: set[int] = set()

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dungeons")

        for _, _, treasure in cursor:
            chests = convert_string_to_treasure(treasure)

            for chest in chests:
                items.add(chest.item)

    return items

def main() -> None:
    """Traverse each dungeon to get the minimum, maximum, and average discovery length"""

if __name__ == "__main__":
    main()
