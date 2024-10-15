from ee23b035_config import HOME_ROW_POS, KB_Type, KB_LAYOUT, T_MIN, ALPHA
from ee23b035_keyboard import REQUIRED_NORMAL_KEYS, REQUIRED_SHIFT_KEYS
from ee23b035_utils import get_key_position, find_key_name, euclidean_dist

import numpy as np

import copy
import math
import random
from typing import Tuple, Generator

def cost_function(text: str, layout: KB_Type) -> float:
    """
    Given a string, and a keyboard layout, calculate the travel distance.
    This is our cost function for the simulated annealing.

    Args:
        text (str): Input string to optimize keyboard for.
        layout (KB_Type): Keyboard layout

    Returns:
        float: Travel distance
    """
    # Map special characters to the key names
    special_chars = {" ": "Space", "\n": "Enter", "\t": "Tab", "\b": "Backspace"}
    travel_dist = 0
    
    for char in text:
        # If the given char is a special char, update the name
        char = special_chars.get(char, char)

        pos, USE_SHIFT = get_key_position(char, layout)
        KEY_LEFT = True  # Indicate which side of the keyboard the key is on

        # Calculate the fastest way to type the key:
        min_dist = euclidean_dist(HOME_ROW_POS[0], pos)
        for idx, neutral_pos in enumerate(HOME_ROW_POS):
            dist = euclidean_dist(neutral_pos, pos)
            if dist < min_dist:
                min_dist = dist
                # idx < 4 -> key would be typed with left hand
                # idx >= 4 -> key would be typed with right hand
                KEY_LEFT = idx < len(HOME_ROW_POS) // 2

        # Account for distance to travel to shift key
        if USE_SHIFT:
            if KEY_LEFT:
                # If key is on left, type shift with right hand
                shift_key = get_key_position("Shift_R", layout)[0]
                min_dist += euclidean_dist(HOME_ROW_POS[-1], shift_key)
            else:
                # If key is on right, type shift with left hand
                shift_key = get_key_position("Shift_L", layout)[0]
                min_dist += euclidean_dist(HOME_ROW_POS[0], shift_key)

        travel_dist += min_dist
    
    return travel_dist


def swap_keys(key_1: str, key_2: str, key_type: str, layout: KB_Type):
    """
    Swap the given keys in a keyboard layout. Modifies the layout in place.

    Args:
        key_1, key_2 (str): Keys to swap
        key_type (str): Type of the keys - shift or regular
        layout (KB_Type): Keyboard layout
    """

    # Find position of the keys to swap
    key_1_row, key_1_col = None, None
    key_2_row, key_2_col = None, None

    for row_name, row in layout.items():
        if key_1 in row.get(key_type, []):
            key_1_row = row_name
            key_1_col = row.get(key_type, []).index(key_1)
        if key_2 in row.get(key_type, []):
            key_2_row = row_name
            key_2_col = row.get(key_type, []).index(key_2)

    # Perform the swap
    layout[key_2_row][key_type] = layout[key_2_row][key_type][:key_2_col] \
                                + key_1 \
                                + layout[key_2_row][key_type][key_2_col + 1:]
    
    layout[key_1_row][key_type] = layout[key_1_row][key_type][:key_1_col] \
                                + key_2 \
                                + layout[key_1_row][key_type][key_1_col + 1:]


def swap_keys_random(layout: KB_Type) -> Tuple[str, str, str]:
    """
    Swap two keys at random in a keyboard layout.
    Modifies the given layout in place

    Args:
        layout: Keyboard layout

    Returns:
        Tuple[str, str, str]: The two keys swapped, and their type (shift or regular)
    """
    # Choose whether we want to swap regular or shift keys
    key_type = random.choice(["keys", "shiftkeys"])
    keys = REQUIRED_NORMAL_KEYS if key_type == "keys" else REQUIRED_SHIFT_KEYS

    # Choose keys and swap
    key_1, key_2 = random.choices(list(keys), k=2)
    swap_keys(key_1, key_2, key_type, layout)

    return key_1, key_2, key_type


def simulated_annealing(text: str, initial_temp: int, layout: KB_Type) -> Generator[float, float, int]:
    """
    Perform simulated annealing on a given keyboard layout to optimize the travel distance.
    Modifies the layout in place to generate the optimum layout.

    Args:
        text (str): Text to optimize for
        initial_temp (int): Initial annealing temperature
        layout (KB_Type): Keyboard layout to optimize

    Returns:
        Generator[float, float, int]: A generator that yields the global minimum travel dist,
            instantaneous travel dist, and instantaneous temperature
    """
    # Temperature variable
    TEMP = initial_temp

    # Deep copy the layout - otherwise the global best will be updated everytime it updates
    global_best = copy.deepcopy(layout)
    global_min = cost_function(text, global_best)

    # Initialise the cost variable
    cost = global_min

    while TEMP > T_MIN:
        # Perform a random swap and compute new cost function
        old_cost = cost
        key_1, key_2, key_type = swap_keys_random(layout)
        cost = cost_function(text, layout)
        diff = cost - old_cost

        # Heuristically choose the new layout if it is worse than the current one
        if not (random.random() < math.exp(-diff / TEMP) or diff < 0):
            swap_keys(key_1, key_2, key_type, layout)
            cost = old_cost

        # Update the global minimum
        if cost < global_min:
            global_best = copy.deepcopy(layout)
            global_min = cost

        # Decrement temperature and yield instantaneous costs
        TEMP = ALPHA * TEMP
        yield global_min, cost, TEMP

    # Update the layout to be the global best
    layout.update(global_best)
