from functools import cache
import json
import os

import cv2

@cache
def get_tiles() -> list[cv2.typing.MatLike]:
    """Return a list of images of all tiles that make up a minimap"""

    path_to_tiles = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/tiles.png")

    tiles = cv2.imread(path_to_tiles)

    return [
        tiles[y:y + 16, x:x + 16]
        for y in range(0, 16*6, 16)
        for x in range(0, 16*8, 16)
    ]

def generate_minimap(map_: list[list[int]]) -> cv2.typing.MatLike:
    """Generate an image of the minimap based on the tile data"""

    MAP_WIDTH = 15
    MAP_HEIGHT = 15

    tiles = get_tiles()

    return cv2.vconcat([cv2.hconcat([tiles[map_[y][x]] for x in range(MAP_HEIGHT)]) for y in range(MAP_WIDTH)])

def main() -> None:
    """Open maps.json and begin creating minimaps"""

    path_to_maps = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/maps.json")

    with open(path_to_maps, "r") as f:
        maps = json.load(f)

    path_to_screenshots = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../build/screenshots/")
    os.makedirs(path_to_screenshots, exist_ok=True)

    for i, map_ in enumerate(maps.values()):
        cv2.imwrite(os.path.join(path_to_screenshots, f"{i}.png"), generate_minimap(map_))

if __name__ == "__main__":
    main()
