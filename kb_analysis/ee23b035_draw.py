from PIL import ImageDraw

from typing import Tuple, Dict, List

from ee23b035_config import KB_H, KB_W, KEY_FONT, KEY_FONT_SIZE
from ee23b035_utils import generate_kb_rows, Position


def first_and_last_keys(
    row: Dict[str, Position]
) -> Tuple[Position, Position, List[Position]]:
    """
    Given a row of keys, separate it into the first, last and middle keys.

    Args:
        row (Dict[str, Position]): Row of keys, with index as the key name and coordinates as value.
            This argument can be used directly from the output of the `ee23b035_utils.generate_kb_rows()` function.

    Returns:
        Position: First key position
        Position: Last key position
        List[Position]: List of keys in between the first and last
    """
    # Calculate first, last and middle keys based on x-coordinate
    first_key = min(row.values(), key=lambda tup: tup[0])[0]
    last_key = max(row.values(), key=lambda tup: tup[0])[0]
    middle_keys = sorted(
        pos[0] for pos in row.values() if pos[0] not in (first_key, last_key)
    )

    return first_key, last_key, list(middle_keys)


def draw_key(
    key: str, left_top: Position, right_bottom: Position, painter: ImageDraw
) -> Position:
    """
    Draw a key on a PIL.ImageDraw object at the given position.

    Args:
        key (str): Text to label the key as
        left_top (Position): xy coordinates of top left corner
        right_bottom (Position): xy coordinates of bottom right corner
        painter (ImageDraw): PIL.ImageDraw object to draw with

    Returns:
        Position: Center point of key bounding box
    """

    # Draw key bounding box
    painter.rounded_rectangle(
        [left_top, right_bottom], radius=5, outline="black", fill="white"
    )

    # Find center of the key
    center_point = (
        (left_top[0] + right_bottom[0]) / 2,
        (left_top[1] + right_bottom[1]) / 2,
    )

    # Draw the key label at the center, accounting for text dimensions
    text_w = painter.textlength(key, font=KEY_FONT)
    painter.text(
        (center_point[0] - text_w / 2, center_point[1] - KEY_FONT_SIZE / 2),
        text=key,
        fill="black",
        font=KEY_FONT,
    )

    return center_point


def draw_keyboard(kb_rows: List[Dict[str, Position]], painter: ImageDraw) -> None:
    """
    Draw keys for a given keyboard layout.

    Args:
        kb_rows (List[Dict[str, Position]]): Row-wise list of keys-position mapping.
            This argument can be directly used from the `ee23b035_utils.generate_kb_rows()` function.
        painter (ImageDraw): Image to draw on
    """

    # Map of key name to key center position
    key_center_map: Dict[str, Position] = {}
    # Current height at which to draw keys
    cum_height = 0

    # Keyboard row height
    KEY_H = KB_H / len(kb_rows)

    for row_num, row in enumerate(kb_rows):

        # Draw key as full width of row if only 1 key in the row
        if len(row) == 1:
            key_name = list(row.keys())[0]
            key_center_map[key_name] = draw_key(
                key_name,
                (1, cum_height + 1),
                (KB_W - 2, cum_height + KEY_H - 1),
                painter,
            )
            continue

        # Extract first, last and middle keys
        first_key, last_key, middle_keys = first_and_last_keys(row)

        # Calculate key width for non-first or last keys
        EFF_KEY_W = KB_W
        KEY_W = 0

        if len(middle_keys) != 0:
            EFF_KB_W = KB_W * (last_key - middle_keys[0]) / (last_key + middle_keys[0])

        # Since I do not know the width of the last key (I can only find out position)
        # I assume it to have same width as the first key.
        # This means that both keys are symmetrically
        # placed about the center of the keyboard.
        OFFSET = (KB_W - EFF_KB_W) / 2

        # Draw first key
        key_name = [key for key in row if row[key][0] == first_key][0]
        key_center_map[key_name] = draw_key(
            key_name[:2],  # Only show first two letters to prevent overflow
            (1, cum_height + 1),
            (OFFSET - 1, cum_height + KEY_H - 1),
            painter,
        )

        # Cumulative width of keys
        cum_width = OFFSET
        # All keys excluding the first
        # We use this to get start and end coordinates for the middle keys
        non_first_keys = middle_keys + [last_key]

        # Draw middle keys
        for i in range(len(middle_keys)):
            KEY_W = (
                EFF_KB_W
                * (non_first_keys[i + 1] - non_first_keys[i])
                / (last_key - middle_keys[0])
            )
            key_name = [key for key in row if row[key][0] == middle_keys[i]][0]
            key_center_map[key_name] = draw_key(
                key_name.upper(),
                (cum_width + 1, cum_height + 1),
                (cum_width + KEY_W - 1, cum_height + KEY_H - 1),
                painter,
            )

            cum_width += KEY_W

        # Draw last key
        key_name = [key for key in row if row[key][0] == last_key][0]
        key_center_map[key_name] = draw_key(
            key_name[:2],  # Only show first two letters to prevent overflow
            (cum_width + 1, cum_height + 1),
            (KB_W - 2, cum_height + KEY_H - 1),
            painter,
        )

        # Update height
        cum_height += KEY_H

    return key_center_map
