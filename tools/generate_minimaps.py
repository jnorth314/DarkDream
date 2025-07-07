from functools import cache
import os
import sqlite3

import cv2

from dungeon import convert_string_to_dungeon, DATABASE_PATH, Dungeon, DungeonTile

TILES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/tiles.png")

def get_tile_ascii(tile: DungeonTile) -> str:
    """Return the ASCII equivalent to the tile"""

    TILES_TO_ASCII = {
        0xFFFFFFFF: [" ", " ", " ", " "],
        0x00000000: ["║", "═", "║", "═"],
        0x00000001: ["╔", "╗", "╝", "╚"],
        0x00000002: ["╬", "╬", "╬", "╬"],
        0x00000003: ["╦", "╣", "╩", "╠"],
        0x00000004: ["╥", "╡", "╨", "╞"],
        0x00000005: ["─", "│", "─", "│"],
        0x00000006: ["│", "─", "│", "─"],
        0x00000007: ["─", "│", "─", "│"],
        0x00000008: ["│", "─", "│", "─"],
        0x00000009: ["╨", "╞", "╥", "╡"],
        0x0000000A: ["╞", "╥", "╡", "╨"],
        0x0000000B: ["╥", "╡", "╨", "╞"],
        0x0000000C: ["╡", "╨", "╞", "╥"],
        0x0000000D: ["┌", "┐", "┘", "└"],
        0x0000000E: ["┐", "┘", "└", "┌"],
        0x0000000F: ["┘", "└", "┌", "┐"],
        0x00000010: ["└", "┌", "┐", "┘"],
        0x00000011: [" ", " ", " ", " "],
        0x00000012: ["╥", "╡", "╨", "╞"],
        0x00000013: ["╡", "╨", "╞", "╥"],
        0x00000014: ["╨", "╞", "╥", "╡"],
        0x00000015: ["╞", "╥", "╡", "╨"],
        0x00000016: ["╫", "╪", "╫", "╪"],
        0x00000017: ["╪", "╫", "╪", "╫"],
        0x00000018: ["╫", "╪", "╫", "╪"],
        0x00000019: ["╪", "╫", "╪", "╫"],
        0x0000001A: ["║", "═", "║", "═"],
        0x0000001B: ["═", "║", "═", "║"],
        0x0000001C: ["║", "═", "║", "═"],
        0x0000001D: ["═", "║", "═", "║"],
        0x0000001E: ["S", "S", "S", "S"],
        0x0000001F: ["E", "E", "E", "E"],
        0x00000020: ["O", "O", "O", "O"],
        0x00000021: ["O", "O", "O", "O"],
        0x00000022: ["O", "O", "O", "O"],
        0x00000023: ["O", "O", "O", "O"],
        0x00000024: ["▀", "▐", "▄", "▌"],
        0x00000025: ["▐", "▄", "▌", "▀"],
        0x00000026: ["▄", "▌", "▀", "▐"],
        0x00000027: ["▌", "▀", "▐", "▄"],
        0x00000028: ["?", "?", "?", "?"],
        0x00000029: ["?", "?", "?", "?"],
        0x0000002A: ["?", "?", "?", "?"],
        0x0000002B: ["?", "?", "?", "?"],
        0x0000002C: ["║", "═", "║", "═"],
        0x0000002D: ["°", "°", "°", "°"],
        0x0000002E: ["°", "°", "°", "°"],
    }

    if tile.id_ not in TILES_TO_ASCII or tile.rotation >= 4:
        raise ValueError(f"Invalid Tile Data ({tile.id_}, {tile.rotation})")

    return TILES_TO_ASCII[tile.id_][tile.rotation]

@cache
def get_tile_image(tile: DungeonTile) -> cv2.typing.MatLike:
    """Get the texture of the tile in the tile sheet"""

    if tile.id_ == 0xFFFFFFFF:
        x, y = 0, 0
    else:
        x, y = 16*tile.rotation, 16*(tile.id_ + 1)

    return cv2.imread(TILES_PATH)[y:y + 16, x:x + 16]

def display_dungeon_map(dungeon: Dungeon) -> None:
    """Print the dungeon to the console"""

    for y in range(15):
        for x in range(15):
            print(
                get_tile_ascii(dungeon[y][x]),
                end=""
            )
        print()

def display_dungeon_image(dungeon: Dungeon) -> None:
    """Display the dungeon minimap in a new window"""

    cv2.imshow(
        "Dungeon Minimap",
        cv2.vconcat([cv2.hconcat([get_tile_image(dungeon[y][x]) for x in range(15)]) for y in range(15)])
    )
    cv2.waitKey(0)

def main() -> None:
    """Generate all screenshots for each dungeon layout"""

    PATH_TO_SCREENSHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/screenshots")

    os.mkdir(PATH_TO_SCREENSHOTS)

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dungeons")

        for seed, layout in cursor:
            dungeon = convert_string_to_dungeon(layout)

            cv2.imwrite(
                f"{PATH_TO_SCREENSHOTS}/{seed:04X}.png",
                cv2.vconcat([cv2.hconcat([get_tile_image(dungeon[y][x]) for x in range(15)]) for y in range(15)])
            )

if __name__ == "__main__":
    main()
