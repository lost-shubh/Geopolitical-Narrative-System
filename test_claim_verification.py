"""
Compatibility wrapper for Stage 4 claim extraction and verification.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline.stage4_fact_discovery import run_stage


def main():
    """Run Stage 4 against the existing Stage 1 output."""
    result = run_stage()
    claims_payload = result["claims_payload"]
    verified_payload = result["verified_payload"]

    print("=" * 70)
    print("STAGE 4 COMPLETE")
    print("=" * 70)
    print(f"Claims extracted: {claims_payload['total_claims']}")
    print(f"Top claims verified: {verified_payload['total_verified']}")
    print(f"Average credibility: {verified_payload['statistics']['average_credibility']}")
    print(f"Claims file: {result['claims_file']}")
    print(f"Verified file: {result['verified_file']}")


if __name__ == "__main__":
    main()
