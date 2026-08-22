"""Command-line entry points for Cage."""

from cage.cli.main import cli, main

# The installed ``cage`` console script points here. It resolves to ``cli`` —
# the wrapper that renders diagnosed failures as a message instead of a
# traceback — while ``main`` stays exported as the raw click group for tests
# and programmatic invocation.
__all__ = ["cli", "main"]
