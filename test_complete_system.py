"""
Complete system smoke test for all five stages.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline.main import run_pipeline


def main():
    """Run the full pipeline using local data and print the resulting files."""
    result = run_pipeline(use_existing_data=True, offline_mode=True)

    print("=" * 70)
    print("COMPLETE SYSTEM TEST FINISHED")
    print("=" * 70)
    print(f"Run summary: {result['summary_file']}")
    print(f"Stage 1 file: {result['stage1']['processed_file']}")
    print(f"Stage 2 file: {result['stage2']['processed_file']}")
    print(f"Stage 3 news file: {result['stage3']['news_file']}")
    print(f"Stage 3 social file: {result['stage3']['social_file']}")
    print(f"Stage 4 verified file: {result['stage4']['verified_file']}")
    print(f"Stage 5 report: {result['stage5']['final_report']}")


if __name__ == "__main__":
    main()
