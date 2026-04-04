"""Wrapper for Stage 5."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.stage5_narrative_synthesis import cli_main


if __name__ == "__main__":
    cli_main()
