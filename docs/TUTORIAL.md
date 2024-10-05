## Installing & Running

1. `pip install -r requirements.txt`
2. `python ./src/main.py`

## How to use!

There are 2 options to using the tool in order to predict dungeons, either manual input or automatically through image recognition.

### Option 1 (Manual)

1. Click a button on the 15x15 grid
2. Click the corresponding tile that fits in that spot.
3. Repeat steps 1-2 until the program finds a match.

### Option 2 (Automatic)

1. Select a capture in the `File` tab with `Select Capture`, I recommend using [OBS's](https://obsproject.com/) Virtual Camera.
2. Optionally in the `View` tab select `Capture Overlay` to overlay the capture on the 15x15 grid.
3. In the `View` tab select `Settings` to bring up settings for cropping the display.
4. Crop the capture region so the 15x15 button grid lines up with the 15x15 grid in-game.
5. Check the `Automate` button to begin the image recognition.
