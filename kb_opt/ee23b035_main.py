"""
Author: Keshav Saravanan, EE23B035

Script to implement simulated annealing on a keyboard layout.

- For configuration options, see ee23b035_config.py
- To see the available CLI flags, run $ python ee23b035_main.py --help
- For details about the implementation, see ee23b035_kb_opt.pdf
"""

import argparse
from typing import List, Tuple, Union

import numpy as np
import matplotlib as mpl
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt
from matplotlib.pyplot import colormaps

from ee23b035_draw import draw_keyboard
from ee23b035_keyboard import REQUIRED_NORMAL_KEYS, REQUIRED_SPECIAL_KEYS
from ee23b035_simulated_annealing import simulated_annealing, cost_function

from ee23b035_config import KB_LAYOUT, HOME_ROW_POS, KB_Type, TEMP
from ee23b035_config import KB_W, KB_H, G_WIDTH, K_PRESS_HMAP_W, CMAP

from ee23b035_utils import Position
from ee23b035_utils import find_key_name, get_key_position
from ee23b035_utils import generate_kb_rows, euclidean_dist


def type_key(char: str, KB_LAYOUT: KB_Type) -> List[str]:
    """
    Return list of keys to be pressed in order to type a character

    Args:
        char (str): Character to be type

    Returns:
        List[str]: List of key names to be pressed
    """

    # Map special characters to the key names
    special_chars = {" ": "Space", "\n": "Enter", "\t": "Tab", "\b": "Backspace"}
    # If the given char is a special char, update the name
    char = special_chars.get(char, char)

    pos, USE_SHIFT = get_key_position(char, KB_LAYOUT)
    KEY_LEFT = True  # Indicate which side of the keyboard the key is on

    # We have to press the key containing char
    yield find_key_name(char, KB_LAYOUT)
    
    num_home_row_keys = len(HOME_ROW_POS)
    col_middle = HOME_ROW_POS[num_home_row_keys // 2][1] + HOME_ROW_POS[num_home_row_keys // 2 - 1][1]
    col_middle = col_middle / 2

    # Account for distance to travel to shift key
    if USE_SHIFT:
        if pos[1] < col_middle:
            # If key is on left, type shift with right hand
            yield "Shift_R" # Also press shift
        else:
            # If key is on right, type shift with left hand
            yield "Shift_L" # Also press shift


def main(text: str, KB_LAYOUT: KB_Type):
    """
    Given a string of text, generate a heatmap visualization for it.

    Args:
        text (str): Input text
    """
    # Generate keyboard image
    image = Image.new("RGB", (KB_W, KB_H), (100, 100, 100))
    painter = ImageDraw.Draw(image)
    key_center_map = draw_keyboard(generate_kb_rows(KB_LAYOUT), painter)

    # Generate heat_map matrix
    # Dimensions: KB_H + K_PRESS_HMAP_W, KB_W + K_PRESS_HMAP_W
    # We will trim off the K_PRESS_HMAP_W later
    # This extra width and length is added so that the full
    # key_press matrix can always fit inside the heat_map matrix
    heat_map = np.zeros((KB_H + K_PRESS_HMAP_W, KB_W + K_PRESS_HMAP_W))

    # Generate key press gaussian
    # This will be superimposed on heat_map whenever a key is pressed
    x, y = np.meshgrid(
        np.linspace(-G_WIDTH, G_WIDTH, K_PRESS_HMAP_W),
        np.linspace(-G_WIDTH, G_WIDTH, K_PRESS_HMAP_W),
    )
    r_sq = x**2 + y**2
    key_press_matrix = np.exp(-r_sq / 2) / (2 * 3.14159)

    # Key press frequency mapping
    key_freq = {key: 0 for key in REQUIRED_NORMAL_KEYS | REQUIRED_SPECIAL_KEYS}

    # Iteratively calculate travel distance
    for char in text:
        to_press = type_key(char, KB_LAYOUT)

        # Update the heat map
        for key_to_press in to_press:
            key_freq[key_to_press] += 1

            x, y = key_center_map[key_to_press]
            x, y = int(x), int(y)
            heat_map[y : y + K_PRESS_HMAP_W, x : x + K_PRESS_HMAP_W] += key_press_matrix

    # PIL.Image to np.array (so we can do a superpose later on)
    img_array = np.array(image)

    # Trim the extra padding
    heat_map = heat_map[
        K_PRESS_HMAP_W // 2 : -K_PRESS_HMAP_W // 2,
        K_PRESS_HMAP_W // 2 : -K_PRESS_HMAP_W // 2,
    ]
    # Normalise from 0 - 1
    heat_map -= heat_map.min()
    heat_map /= heat_map.max()
    heat_map = CMAP(heat_map)[:, :, :3] * 255  # CMAP returns RGBA, we don't want the A

    # Superimpose heatmap on top of keyboard
    combined_img = img_array & heat_map.astype(np.uint8)

    # Show image with colorbar
    img_fig = plt.imshow(
        combined_img, vmin=min(key_freq.values()), vmax=max(key_freq.values())
    )


    plt.set_cmap(CMAP)
    plt.colorbar(orientation="horizontal", pad=0.01)

    # Remove axes - we only want the image
    img_fig.axes.get_xaxis().set_visible(False)
    img_fig.axes.get_yaxis().set_visible(False)
    plt.axis("off")

    return key_freq


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python main.py")

    parser.add_argument(
        "-f",
        "--filename",
        default="text_data.txt",
        help="File to read from",
        required=False,
    )

    parser.add_argument(
        "-i",
        "--ignore_spaces",
        default=False,
        action="store_true",
        required=False,
        help="Ignore spaces in the file",
    )

    parser.add_argument(
        "-o",
        "--output_file",
        default="heatmap.png",
        required=False,
        help="Output file name",
    )

    args = parser.parse_args()

    with open(args.filename) as f:
        text = f.read()
        if args.ignore_spaces:
            text = text.replace(" ", "")

    # First, calculate the travel_dist for the unoptimized layout
    unoptimized_travel_dist = cost_function(text, KB_LAYOUT)
    print(f"Unoptimized Travel Distance {unoptimized_travel_dist:.3f}")

    # Optimize the keyboard layout
    for best_dist, curr_dist, temp in simulated_annealing(text, TEMP, KB_LAYOUT):
        print(f"Temperature: {temp:.3f}", end="\r")

    travel_dist = cost_function(text, KB_LAYOUT)
    key_freq = main(text, KB_LAYOUT)

    print(f"Optimized Travel Distance: {travel_dist:.3f}")

    # Display key press frequency
    print("Key Press Frequency:")

    counter = 1
    for key in sorted(REQUIRED_NORMAL_KEYS):
        freq = key_freq[key]
        if counter % 10 != 0:
            print(f"{key} {freq}", end="\t")
        else:
            print(f"{key} {freq}")
        counter += 1

    print()

    # Special keys at the end
    for key in sorted(REQUIRED_SPECIAL_KEYS):
        print(f"{key}: {key_freq[key]}")

    plt.title(f"Optimized Travel Distance: {travel_dist:.3f}")
    plt.savefig(args.output_file, bbox_inches="tight", dpi=200)
