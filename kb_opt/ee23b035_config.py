from typing import Dict, Union, List, Tuple

import matplotlib as mpl
from PIL import ImageFont

from ee23b035_keyboard_layouts import QWERTY_LAYOUT, DVORAK_LAYOUT, COLEMAK_LAYOUT

# Keyboard layout data type
KB_Type = Dict[str, Dict[str, Union[str, List[Tuple[float, int]]]]]

KB_LAYOUT: KB_Type = QWERTY_LAYOUT

HOME_ROW_POS = [
    (1.75, 2),
    (2.75, 2),
    (3.75, 2),
    (4.75, 2),
    (7.75, 2),
    (8.75, 2),
    (9.75, 2),
    (10.75, 2),
]

HOME_ROW_POS.sort(key=lambda t: t[0])

# Keyboard image characteristics
KB_W = 1000
KB_H = 350
KEY_FONT_SIZE = 20
KEY_FONT = ImageFont.truetype("arial.ttf", KEY_FONT_SIZE)

# Width of gaussian to superimpose on key when pressed
G_WIDTH = 3.5
# Size of gaussian array - larger = more spread
K_PRESS_HMAP_W = 200
# Color gradient to use for heat map
CMAP = mpl.colormaps["turbo"]

# Initial temperature for annealing:
TEMP = 10000
# Scale factor
ALPHA = 0.99
# Minimum temperature
T_MIN = 1
