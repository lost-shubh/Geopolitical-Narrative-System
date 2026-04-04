"""Wrapper for running the full pipeline from the project root."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.main import cli_main


if __name__ == "__main__":
    cli_main()
