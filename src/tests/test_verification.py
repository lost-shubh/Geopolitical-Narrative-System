"""Pytest coverage for the offline verification pipeline."""

from src.analysis.claim_extraction import ClaimExtractor
from src.verification.fact_checker import FactChecker


def test_claim_extraction_finds_candidate_claims():
    extractor = ClaimExtractor()
    claims = extractor.extract_claims_from_text(
        "Officials said 12 civilians were injured in 2026 after the attack on Monday."
    )

    assert claims
    assert claims[0]["has_numbers"] is True
    assert claims[0]["verifiability_score"] > 0


def test_fact_checker_returns_ranked_evidence():
    checker = FactChecker(
        articles=[
            {
                "title": "Ukraine attacking Russian gas pipeline to stop deliveries to Europe",
                "description": "Russia's defense ministry said deliveries were targeted.",
                "content": "The ministry said the pipeline infrastructure was attacked.",
                "source": "RT",
                "url": "https://example.test/pipeline",
            }
        ]
    )
    result = checker.verify_claim(
        {
            "text": "Ukraine attacked a Russian gas pipeline.",
            "type": "factual_claim",
            "entities": {"GPE": ["Ukraine", "Russia"]},
        }
    )

    assert result["evidence_count"] > 0
    assert result["verification_status"] in {"likely_true", "needs_verification", "disputed"}
