"""Shared Layer-2 base classes reused across example benchmarks.

Currently hosts the CTF benchmark family (``xbow`` / ``nyu_ctf`` / ``hackworld``).
"""

from examples.base.ctf import (
    DEFAULT_FLAG_PATTERN,
    CtfBenchmark,
    FlagScorer,
    extract_flag_candidates,
    first_text,
)

__all__ = [
    "CtfBenchmark",
    "FlagScorer",
    "DEFAULT_FLAG_PATTERN",
    "extract_flag_candidates",
    "first_text",
]
