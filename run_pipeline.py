"""
Compatibility entrypoint for the full pipeline.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline.main import cli_main


if __name__ == "__main__":
    cli_main()
