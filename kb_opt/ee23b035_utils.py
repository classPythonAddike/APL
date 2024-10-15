from PIL import ImageFont

from typing import Tuple, Union, Dict, List

from ee23b035_keyboard import KB_Type
from ee23b035_config import KB_H, KB_W, KEY_FONT, KEY_FONT_SIZE

# Position type - (x, y)
Position = Tuple[float, float]


def euclidean_dist(pos1: Position, pos2: Position) -> float:
    """Calculate euclidean distance between two points."""
    return ((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2) ** 0.5


def generate_kb_rows(layout: KB_Type) -> List[Dict[str, Position]]:
    """
    Given a Keyboard Layout dictionary, generate a list of rows of keys,
    Each row being a dictionary of key -> position on that row.

    Args:
        layout (Dict[str, Dict]): Keyboard layout dictionary

    Returns:
        List[Dict[str, Position]]: List of key->position maps for each row
    """

    # Populate list with non-special keys
    kb_rows = [
        {row["keys"][idx]: row["positions"][idx] for idx in range(len(row["keys"]))}
        for _, row in sorted(layout.items(), key=lambda t: t[0])
        if row.get("keys", None) is not None
    ]

    # Add special keys
    for key, pos in layout["special_keys"].items():
        # If the row for this key exists, add it into the row
        if pos[1] < len(kb_rows):
            kb_rows[pos[1]][key] = pos
        # Else, keep adding empty rows
        else:
            while pos[1] >= len(kb_rows):
                kb_rows.append({})
            kb_rows[pos[1]][key] = pos

    return kb_rows


def find_key_name(key: str, layout: KB_Type) -> str:
    """
    Given a character to be typed, find the key name to be pressed

    Args:
        key (str): Character to type
        layout (KB_Type): Keyboard Layout

    Returns:
        str: Key name

    Raises:
        ValueError if the key is not found
    """
    for row in layout.values():
        if key in row.get("keys", []):
            return key
        elif key in row.get("shiftkeys", []):
            index = row["shiftkeys"].index(key)
            return row["keys"][index]

    if key in layout.get("special_keys", []):
        return key

    raise ValueError(f"Key '{key}' not found")


def get_key_position(key: str, layout: KB_Type) -> Tuple[str, bool]:
    """
    Given a character to be typed, find the key position

    Args:
        key (str): Character to type
        layout (KB_Type): Keyboard Layout

    Returns:
        str: Key name
        bool: If shift needs to be pressed

    Raises:
        ValueError if the key is not found
    """
    for row in layout.values():
        if key in row.get("keys", []):
            index = row["keys"].index(key)
            return row["positions"][index], False
        elif key in row.get("shiftkeys", []):
            index = row["shiftkeys"].index(key)
            return row["positions"][index], True

    if key in layout.get("special_keys", []):
        return layout["special_keys"][key], False

    raise ValueError(f"Key '{key}' not found")
