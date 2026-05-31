"""Pytest coverage for the offline verification pipeline."""

from src.analysis.claim_extraction import ClaimExtractor
from src.verification.fact_checker import FactChecker
from src.verification.google_factcheck import GoogleFactCheckSearch


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


def test_google_factcheck_search_normalizes_claim_reviews():
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "claims": [
                    {
                        "text": "A viral post claimed a treaty had been signed.",
                        "claimant": "viral post",
                        "claimReview": [
                            {
                                "publisher": {"name": "FactCheck.org"},
                                "title": "No treaty was signed",
                                "url": "https://example.test/fact-check",
                                "textualRating": "False",
                                "reviewDate": "2026-04-05T00:00:00Z",
                            }
                        ],
                    }
                ]
            }

    class FakeSession:
        def get(self, url, params, timeout):
            assert "claims:search" in url
            assert params["key"] == "test-key"
            assert params["pageSize"] == 2
            assert timeout == 10
            return FakeResponse()

    search = GoogleFactCheckSearch(api_key="test-key", session=FakeSession())
    results = search.search("treaty signed", max_results=2)

    assert results[0]["evidence_type"] == "google_factcheck"
    assert results[0]["source"] == "FactCheck.org"
    assert results[0]["stance"] == "contradict"


def test_fact_checker_includes_external_factcheck_evidence():
    class FakeExternalFactcheck:
        def search(self, query, max_results):
            assert query.startswith("fact check")
            return [
                {
                    "title": "External review",
                    "source": "FactCheck.org",
                    "url": "https://example.test/review",
                    "snippet": "External review says the claim is false.",
                    "credibility_score": 0.9,
                    "relevance_score": 0.95,
                    "stance": "contradict",
                    "evidence_type": "google_factcheck",
                }
            ]

    checker = FactChecker(articles=[], external_factcheck=FakeExternalFactcheck())
    result = checker.verify_claim({"text": "A treaty was signed.", "type": "factual_claim"})

    assert any(item["evidence_type"] == "google_factcheck" for item in result["evidence"])
