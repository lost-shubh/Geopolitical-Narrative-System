"""
Fact Checking Module - Stage 4b.
Ranks local and research-style evidence to verify or debunk claims.
"""

from pathlib import Path
import json
from typing import Dict, List, Sequence

from .evidence_ranker import EvidenceRanker
from .fact_finder import FactFinder
from .google_factcheck import GoogleFactCheckSearch
from .research_search import ResearchSearch


class FactChecker:
    """Search for factual evidence to verify claims."""

    def __init__(
        self,
        articles: Sequence[Dict] | None = None,
        external_factcheck: GoogleFactCheckSearch | None = None,
        enable_external_factcheck: bool = True,
    ):
        """Initialize fact checker."""
        print("Initializing fact checker...")
        self.search_results_cache = {}
        self.fact_finder = FactFinder(articles=articles)
        self.research_search = ResearchSearch()
        self.external_factcheck = (
            external_factcheck
            if external_factcheck is not None
            else GoogleFactCheckSearch.from_config()
        )
        if not enable_external_factcheck:
            self.external_factcheck = GoogleFactCheckSearch(enabled=False)
        self.ranker = EvidenceRanker()

    def search_web(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search for information about a claim.

        This project uses local article matching plus a small curated
        research-style knowledge base so the pipeline can run offline.
        """
        if query in self.search_results_cache:
            return self.search_results_cache[query]

        print(f"  Searching for: {query[:60]}...")
        local_evidence = self.fact_finder.search_claim(query, max_results=max_results)
        research_evidence = self.research_search.search(query, max_results=max_results)
        external_evidence = self.external_factcheck.search(query, max_results=max_results)
        results = self.ranker.rank(local_evidence + research_evidence + external_evidence, max_results=max_results)

        self.search_results_cache[query] = results
        return results

    def verify_claim(self, claim: Dict) -> Dict:
        """Attempt to verify a single claim."""
        claim_text = claim.get("text", "")
        claim_type = claim.get("type", "unknown")
        entities = claim.get("entities", {})
        search_query = self._create_search_query(claim_text)

        local_evidence = self.fact_finder.search_claim(claim_text, claim_type=claim_type, max_results=6)
        research_evidence = self.research_search.search(claim_text, entities=entities, max_results=3)
        external_evidence = self.external_factcheck.search(search_query, max_results=3)
        evidence = self.ranker.rank(local_evidence + research_evidence + external_evidence, max_results=5)

        avg_credibility = sum(item["credibility_score"] for item in evidence) / len(evidence) if evidence else 0.0
        support_weight = sum(item["credibility_score"] for item in evidence if item.get("stance") == "support")
        contradict_weight = sum(item["credibility_score"] for item in evidence if item.get("stance") == "contradict")

        if contradict_weight > support_weight * 1.15:
            status = "disputed"
        elif support_weight >= contradict_weight and avg_credibility > 0.78 and len(evidence) >= 2:
            status = "likely_true"
        else:
            status = "needs_verification"

        return {
            "claim": claim_text,
            "claim_type": claim_type,
            "verification_status": status,
            "credibility_score": round(avg_credibility, 2),
            "evidence_count": len(evidence),
            "evidence": evidence,
            "entities": entities,
            "search_query": search_query,
        }

    def _create_search_query(self, claim_text: str) -> str:
        """Create an optimized search query from a claim."""
        words = claim_text.split()[:10]
        query = " ".join(words)
        return f"fact check {query}"

    def verify_multiple_claims(self, claims: List[Dict]) -> List[Dict]:
        """Verify multiple claims."""
        print(f"\nVerifying {len(claims)} claims...")
        verified = []

        for index, claim_item in enumerate(claims, 1):
            print(f"[{index}/{len(claims)}] Verifying claim...")

            if "claim" in claim_item:
                claim = claim_item["claim"]
            else:
                claim = claim_item

            result = self.verify_claim(claim)

            if "source_title" in claim_item:
                result["original_source"] = {
                    "title": claim_item.get("source_title", ""),
                    "url": claim_item.get("source_url", ""),
                    "source": claim_item.get("source", ""),
                }

            verified.append(result)

        print("Verification complete")
        return verified

    def get_verification_statistics(self, verified_claims: List[Dict]) -> Dict:
        """Get statistics about verification results."""
        total = len(verified_claims)
        if total == 0:
            return {}

        status_counts = {}
        for claim in verified_claims:
            status = claim["verification_status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        avg_credibility = sum(item["credibility_score"] for item in verified_claims) / total

        return {
            "total_verified": total,
            "status_breakdown": status_counts,
            "average_credibility": round(avg_credibility, 2),
            "high_credibility_count": sum(1 for item in verified_claims if item["credibility_score"] > 0.8),
            "disputed_count": sum(1 for item in verified_claims if item["verification_status"] == "disputed"),
        }


def main():
    """Run fact checking on extracted claims."""
    print("=" * 70)
    print("STAGE 4B: FACT VERIFICATION")
    print("=" * 70)

    input_file = "data/processed/claim_extraction/extracted_claims.json"

    if not Path(input_file).exists():
        print(f"\nError: {input_file} not found")
        print("Please run Stage 4a first (claim extraction):")
        print("  python src/analysis/claim_extraction.py")
        return

    print(f"\nLoading claims from: {input_file}")
    with open(input_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    top_claims = data.get("top_claims", [])
    articles = [article for article in data.get("articles", [])]

    if not top_claims:
        print("No claims found in file")
        return

    print(f"Loaded {len(top_claims)} top claims")

    fact_checker = FactChecker(articles=articles)
    verified_claims = fact_checker.verify_multiple_claims(top_claims[:10])

    print("\n" + "=" * 70)
    print("VERIFICATION STATISTICS")
    print("=" * 70)

    stats = fact_checker.get_verification_statistics(verified_claims)

    print(f"\nTotal claims verified: {stats['total_verified']}")
    print(f"Average credibility: {stats['average_credibility']}")
    print(f"High credibility (>0.8): {stats['high_credibility_count']}")
    print(f"Disputed: {stats['disputed_count']}")

    print("\nVerification status breakdown:")
    for status, count in sorted(stats["status_breakdown"].items()):
        pct = (count / stats["total_verified"]) * 100
        print(f"  {status:20s}: {count} ({pct:.1f}%)")

    output_dir = Path("data/processed/fact_verification")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "verified_claims.json"

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump({
            "total_verified": len(verified_claims),
            "statistics": stats,
            "verified_claims": verified_claims,
        }, handle, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("FACT VERIFICATION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
