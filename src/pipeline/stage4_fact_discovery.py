"""
Stage 4: claim extraction and evidence-based verification.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analysis.claim_extraction import ClaimExtractor
from src.verification.fact_checker import FactChecker
from src.utils.api_clients import load_model_config


def _load_stage_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_stage(*, stage1_result: Dict | None = None, top_n_claims: int = 10) -> Dict:
    """Run claim extraction and fact verification."""
    model_config = load_model_config()

    if stage1_result is None:
        stage1_result = _load_stage_json("data/processed/stage1_content_extraction/articles_with_context.json")

    articles = stage1_result.get("articles", [])
    extractor = ClaimExtractor(model_name=model_config["spacy_model"])
    analyzed_articles = extractor.extract_claims_from_articles(articles)
    top_claims = extractor.get_top_claims(analyzed_articles, n=top_n_claims)

    fact_checker = FactChecker(articles=articles)
    verified_claims = fact_checker.verify_multiple_claims(top_claims)
    verification_stats = fact_checker.get_verification_statistics(verified_claims)

    output_dir = Path("data/processed/stage4_fact_discovery")
    output_dir.mkdir(parents=True, exist_ok=True)
    claims_file = output_dir / "extracted_claims.json"
    verified_file = output_dir / "verified_claims.json"

    claims_payload = {
        "total_articles": len(analyzed_articles),
        "total_claims": sum(article["claim_count"] for article in analyzed_articles),
        "top_claims": top_claims,
        "articles": analyzed_articles,
    }
    verified_payload = {
        "total_verified": len(verified_claims),
        "statistics": verification_stats,
        "verified_claims": verified_claims,
    }

    with open(claims_file, "w", encoding="utf-8") as handle:
        json.dump(claims_payload, handle, indent=2, ensure_ascii=False)
    with open(verified_file, "w", encoding="utf-8") as handle:
        json.dump(verified_payload, handle, indent=2, ensure_ascii=False)

    legacy_claims_dir = Path("data/processed/claim_extraction")
    legacy_claims_dir.mkdir(parents=True, exist_ok=True)
    with open(legacy_claims_dir / "extracted_claims.json", "w", encoding="utf-8") as handle:
        json.dump(claims_payload, handle, indent=2, ensure_ascii=False)

    legacy_verified_dir = Path("data/processed/fact_verification")
    legacy_verified_dir.mkdir(parents=True, exist_ok=True)
    with open(legacy_verified_dir / "verified_claims.json", "w", encoding="utf-8") as handle:
        json.dump(verified_payload, handle, indent=2, ensure_ascii=False)

    return {
        "claims_file": str(claims_file),
        "verified_file": str(verified_file),
        "claims_payload": claims_payload,
        "verified_payload": verified_payload,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage 4 fact discovery.")
    parser.add_argument("--top-claims", type=int, default=10, help="Number of top claims to verify")
    return parser


def cli_main() -> Dict:
    args = build_parser().parse_args()
    result = run_stage(top_n_claims=args.top_claims)
    print("Stage 4 complete.")
    print(f"Claims file: {result['claims_file']}")
    print(f"Verified file: {result['verified_file']}")
    return result


if __name__ == "__main__":
    cli_main()
