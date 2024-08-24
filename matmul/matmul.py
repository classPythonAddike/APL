from typing import List, Union, get_args

# Numeric data type
Numeric = Union[int, float, complex]


def multiply(row1: List[Numeric], row2: List[Numeric]) -> Numeric:
    """
    Elementwise multiplication of 2 rows.
    The rows are guaranteed to have same dimensions, so no checks are performed.

    Parameters:
     - row1: List of numerical data
     - row2: List of numerical data, of same length as row1

    Returns:
     - Elementwise multiplication accumulated along the row
    """
    return sum(i * j for i, j in zip(row1, row2))


def matrix_multiply(
    matrix1: List[List[Numeric]], matrix2: List[List[Numeric]]
) -> List[List[Numeric]]:
    """
    Multiplies two 2D matrices

    Parameters:
     - matrix1: A 2D matrix of numerical data
     - matrix2: A 2D matrix of numerical data

    Returns:
     - The matrix product of the two matrices

    Checks:
     - Matrices have atleast 1 dimension
     - Matrices have atleast 1 row
     - Matrices have atleast 2 dimensions
     - Matrices have atleast 1 column
     - All rows must have same length
     - Datatypes are numeric
     - Matrices have dimensions of form n x k and k x m

    If the two matrices satisfy the above conditions, the product of the two matrices is returned.
    Otherwise, an exception is raised.
    """

    # Array of checks in (Callable, Exception, ErrorMessage) format
    # Much easier to add/modify/delete checks this way
    checks = [
        (
            lambda matrix: hasattr(matrix, "__iter__"),
            ValueError,
            "Must have atleast 1 dim",
        ),
        (
            lambda matrix: len(matrix) > 0,
            ValueError,
            "Must have atleast 1 row"
        ),
        (
            lambda matrix: all(hasattr(i, "__iter__") for i in matrix),
            ValueError,
            "Must have atleast 2 dims",
        ),
        (
            lambda matrix: len(matrix[0]) > 0,
            ValueError,
            "Must have atleast 1 col"
        ),
        (
            lambda matrix: all(len(i) == len(matrix[0]) for i in matrix),
            ValueError,
            "Rows must have same len",
        ),
        (
            lambda matrix: all(
                all(isinstance(j, get_args(Numeric)) for j in i) for i in matrix
            ),
            TypeError,
            "Must contain only numeric data",
        ),
    ]

    # Apply the checks to the parameters
    for check, error, message in checks:
        if not (check(matrix1) and check(matrix2)):
            raise error(message)

    # Final check to see if the matrices have compatible dimensions
    if len(matrix1) != len(matrix2[0]):
        raise ValueError("Matrices cannot be multiplied")

    # Transpose matrix2, now we're multiplying rows by rows (easier to index)
    matrix2_transpose = [[row[i] for row in matrix2] for i in range(len(matrix2[0]))]

    # Placeholder matrix for the multiplication result
    resultant_matrix = [[0] * len(matrix2_transpose) for j in range(len(matrix1))]

    # Elementwise multiplication
    for i in range(len(matrix1)):
        for j in range(len(matrix2_transpose)):
            resultant_matrix[i][j] = multiply(matrix1[i], matrix2_transpose[j])

    return resultant_matrix
