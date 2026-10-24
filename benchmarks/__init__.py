"""
benchmarks package — reproducible performance measurement engine for Connect-4 DAA platform.
"""

from benchmarks.positions import (
    BenchmarkPosition,
    BENCHMARK_POSITIONS,
    get_position,
    list_positions,
)
from benchmarks.runner import (
    run_position_benchmark,
    run_depth_scaling_benchmark,
)

__all__ = [
    "BenchmarkPosition",
    "BENCHMARK_POSITIONS",
    "get_position",
    "list_positions",
    "run_position_benchmark",
    "run_depth_scaling_benchmark",
]
