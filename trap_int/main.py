from trap_py import py_trapz
from trap_np import np_trapz

import numpy as np

import timeit
import argparse
import setuptools
from typing import Callable, Dict

def f_sq(x: float) -> float:
    return x ** 2

def f_sin(x: float) -> float:
    return np.sin(x)

IMPLEMENTATIONS = {
    "np": np_trapz,
    "py": py_trapz
}

FUNCTIONS = {
    "sq": f_sq,
    "sin": f_sin
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Benchmark trapezoidal integration across pure Python, Cython, and NumPy."
    )

    parser.add_argument(
        '-i',
        nargs='+',
        default=IMPLEMENTATIONS.keys(),
        choices=IMPLEMENTATIONS.keys(),
        help="select implementations to benchmark"
    )
    parser.add_argument(
        '-f',
        nargs='+',
        default=FUNCTIONS.keys(),
        choices=FUNCTIONS.keys(),
        help="select functions to benchmark on"
    )

    args = parser.parse_args()
    
    for f_name in args.f:
        func = FUNCTIONS[f_name]
        print(f"Benchmarking for function {f_name}():")
        for impl_name in args.i:
            implementation = IMPLEMENTATIONS[impl_name]

            timer = timeit.Timer(
                f"impl(f, {1}, {2}, {1000})",
                globals={
                    "impl": implementation,
                    "f": func
                }
            )

            exec_time = timer.autorange()
            t = exec_time[1] / exec_time[0] * 1e6

            print(f"Implementation: {impl_name}\t Time: {t:10.3f} us")
