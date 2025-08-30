import multiprocessing
import os
import sqlite3

import cv2

from dungeon import (
    convert_string_to_layout, convert_string_to_treasure, DATABASE_PATH, DungeonLayout, DungeonTile, DungeonTreasure,
    get_tile_image, get_treasure_overlay, USED_DUNGEON_TILES
)

PATH_TO_SCREENSHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/screenshots")

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

def display_dungeon_map(dungeon: DungeonLayout) -> None:
    """Print the dungeon to the console"""

    for y in range(15):
        for x in range(15):
            print(
                get_tile_ascii(dungeon[y][x]),
                end=""
            )
        print()

def display_dungeon_image(layout: DungeonLayout, treasure: DungeonTreasure) -> None:
    """Display the dungeon minimap in a new window"""

    cv2.imshow(
        "Dungeon Minimap",
        cv2.add(cv2.cvtColor(get_minimap(layout), cv2.COLOR_BGR2BGRA), get_treasure_overlay(treasure))
    )
    cv2.waitKey(0)

def get_minimap(layout: DungeonLayout) -> cv2.typing.MatLike:
    """Convert the layout into a minimap image"""

    return cv2.vconcat([cv2.hconcat([get_tile_image(layout[y][x]) for x in range(15)]) for y in range(15)])

def create_dungeon_image(seed: int, layout_as_str: str, treasure_as_str: str) -> None:
    """Create an image based on the dungeon parameters"""

    layout, treasure = convert_string_to_layout(layout_as_str), convert_string_to_treasure(treasure_as_str)
    cv2.imwrite(f"{PATH_TO_SCREENSHOTS}/{seed:04X}.png",
                cv2.add(cv2.cvtColor(get_minimap(layout), cv2.COLOR_BGR2BGRA), get_treasure_overlay(treasure)))

def main() -> None:
    """Generate all screenshots for each dungeon layout"""

    if not os.path.exists(PATH_TO_SCREENSHOTS):
        os.mkdir(PATH_TO_SCREENSHOTS)

    cv2.imwrite(
        f"{PATH_TO_SCREENSHOTS}/example_tiles.png",
        cv2.hconcat([get_tile_image(tile)
                     for tile in sorted(USED_DUNGEON_TILES, key=lambda t: (((t.id_ + 1) & 0xFF) << 2) + t.rotation)])
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dungeons")

        with multiprocessing.Pool() as pool:
            pool.starmap(create_dungeon_image, cursor)

if __name__ == "__main__":
    main()
