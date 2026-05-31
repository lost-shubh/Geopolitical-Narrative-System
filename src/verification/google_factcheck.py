"""
Optional Google Fact Check Tools API integration.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

from src.utils.api_clients import load_api_config

from .source_credibility import SourceCredibilityScorer


class GoogleFactCheckSearch:
    """Fetch claim-review evidence from Google Fact Check Tools when configured."""

    ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def __init__(
        self,
        *,
        api_key: str = "",
        enabled: bool = True,
        session: Any | None = None,
        timeout_seconds: int = 10,
    ):
        self.api_key = api_key.strip()
        self.enabled = enabled and bool(self.api_key)
        self.session = session or requests
        self.timeout_seconds = timeout_seconds
        self.credibility = SourceCredibilityScorer()

    @classmethod
    def from_config(cls) -> "GoogleFactCheckSearch":
        config = load_api_config()
        env_name = config.get("google_factcheck_env", "GOOGLE_FACTCHECK_API_KEY")
        api_key = os.getenv(env_name, config.get("google_factcheck_api_key", ""))
        return cls(
            api_key=api_key,
            enabled=bool(config.get("enable_google_factcheck", True)),
        )

    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Return normalized fact-check review evidence for a claim."""
        if not self.enabled or not query.strip():
            return []

        try:
            response = self.session.get(
                self.ENDPOINT,
                params={"query": query, "key": self.api_key, "pageSize": max_results},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        evidence: List[Dict] = []
        for claim in payload.get("claims", []):
            claim_text = claim.get("text", "")
            for review in claim.get("claimReview", [])[:max_results]:
                publisher = review.get("publisher") or {}
                source = publisher.get("name") or publisher.get("site") or "Google Fact Check"
                rating = review.get("textualRating", "")
                title = review.get("title") or claim_text or "Fact-check review"
                url = review.get("url", "")
                evidence.append(
                    {
                        "title": title,
                        "source": source,
                        "url": url,
                        "snippet": self._snippet(claim_text, rating),
                        "credibility_score": max(0.82, self.credibility.score(source, url)),
                        "relevance_score": 0.9,
                        "stance": self._stance_from_rating(rating),
                        "evidence_type": "google_factcheck",
                        "claimant": claim.get("claimant", ""),
                        "claim_date": claim.get("claimDate", ""),
                        "reviewed_at": review.get("reviewDate", ""),
                        "textual_rating": rating,
                    }
                )
                if len(evidence) >= max_results:
                    return evidence
        return evidence

    def _snippet(self, claim_text: str, rating: str) -> str:
        if claim_text and rating:
            return f"{claim_text} Rating: {rating}."
        return claim_text or (f"Rating: {rating}." if rating else "External fact-check review.")

    def _stance_from_rating(self, rating: str) -> str:
        lowered = rating.lower()
        if any(token in lowered for token in ("false", "misleading", "incorrect", "untrue", "pants on fire")):
            return "contradict"
        if any(token in lowered for token in ("true", "correct", "accurate", "verified")):
            return "support"
        return "neutral"
