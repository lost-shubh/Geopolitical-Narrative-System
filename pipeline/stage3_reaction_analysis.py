"""Wrapper for Stage 3."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.stage3_reaction_analysis import cli_main


if __name__ == "__main__":
    cli_main()
