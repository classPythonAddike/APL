from typing import Dict, List, Tuple, Union

from ee23b035_config import KB_Type, KB_LAYOUT

REQUIRED_NORMAL_KEYS = set("zxcvbnm,./asdfghjkl;'qwertyuiop[]\\`1234567890-=")
REQUIRED_SHIFT_KEYS = set('ZXCVBNM<>?ASDFGHJKL:"QWERTYUIOP{}|~!@#$%^&*()_+')
REQUIRED_SPECIAL_KEYS = {
    "Shift_L",
    "Shift_R",
    "Space",
    "Backspace",
    "Tab",
    "CapsLock",
    "Enter",
}

REQUIRED_KEYS = REQUIRED_NORMAL_KEYS | REQUIRED_SHIFT_KEYS | REQUIRED_SPECIAL_KEYS


def validate_kb_layout(LAYOUT: KB_Type):
    """
    Check if a given keyboard layout is valid

    Args:
        LAYOUT (KB_Type): The keyboard layout

    Raises:
        AssertionError if the keyboard is of invalid format
    """
    all_keys = set()
    row_nums = set()

    for row_name, row in LAYOUT.items():
        if row.get("keys") is not None:
            # If keys is present, shiftkeys should also exist
            assert row.get("shiftkeys") is not None, "Could not find shiftkeys"

            # Number of shitfkeys = number of keys = number of position tuples
            assert len(row["keys"]) == len(
                row["shiftkeys"]
            ), "Variable length in keys and shiftkeys"
            assert len(row["keys"]) == len(
                row["positions"]
            ), "Variable length in keys and positions"

            all_keys.update(row["keys"])
            all_keys.update(row["shiftkeys"])

            row_nums.add(row["positions"][0][1])
        elif row_name == "special_keys":
            all_keys.update(row)
            row_nums.update([pos[1] for pos in row.values()])

    # Missing keys
    assert REQUIRED_KEYS.issubset(
        all_keys
    ), f"Not all required keys are present: {REQUIRED_KEYS - all_keys}"

    # Ensure row numbers are integers and no missing rows

    assert isinstance(min(row_nums), int) and isinstance(
        max(row_nums), int
    ), "Non-integer rows present in keyboard"

    assert min(row_nums) == 0, "First row must have row number 0"

    assert list(sorted(row_nums)) == list(
        range(min(row_nums), max(row_nums) + 1)
    ), "Non-integer/empty rows present in keyboard"


validate_kb_layout(KB_LAYOUT)
