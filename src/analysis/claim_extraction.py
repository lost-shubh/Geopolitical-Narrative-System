"""
Claim Extraction Module - Stage 4.
Extracts verifiable factual claims from news articles using NLP with a
regex-based fallback when spaCy models are unavailable.
"""

from pathlib import Path
import json
import re
from typing import Dict, List

try:
    import spacy
except Exception:  # pragma: no cover - optional dependency failure
    spacy = None


class ClaimExtractor:
    """Extract factual claims from text using NLP and heuristics."""

    CLAIM_VERBS = {
        "say", "said", "claim", "claims", "claimed", "state", "states", "stated",
        "report", "reports", "reported", "announce", "announced", "confirm", "confirmed",
        "reveal", "revealed", "declare", "declared", "assert", "asserted",
        "allege", "alleged", "accuse", "accused", "deny", "denied",
    }

    FACTUAL_PATTERNS = [
        r"\b\d+\s*(people|civilians|soldiers|casualties)",
        r"\b\d+\s*(percent|%)",
        r"(increased|decreased|rose|fell)\s+by\s+\d+",
        r"on\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
        r"in\s+\d{4}",
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}",
    ]

    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize claim extractor."""
        self.nlp = None
        self.sentencizer = None

        if spacy is not None:
            try:
                print(f"Loading spaCy model: {model_name}...")
                self.nlp = spacy.load(model_name)
                print("Model loaded")
            except Exception as exc:
                print(f"Falling back to regex claim extraction: {exc}")
                try:
                    self.sentencizer = spacy.blank("en")
                    self.sentencizer.add_pipe("sentencizer")
                except Exception:
                    self.sentencizer = None

    def extract_claims_from_text(self, text: str) -> List[Dict]:
        """Extract claims from a single text."""
        if not text or not text.strip():
            return []

        doc = self._to_doc(text)
        claims = []

        for sent in self._iter_sentences(doc, text):
            sent_text = sent.text.strip()

            if len(sent_text.split()) < 5:
                continue

            has_claim_verb = self._sentence_has_claim_verb(sent)
            has_factual_pattern = any(re.search(pattern, sent_text, re.IGNORECASE) for pattern in self.FACTUAL_PATTERNS)
            has_quote = '"' in sent_text or "'" in sent_text

            if has_claim_verb or has_factual_pattern or has_quote:
                claim_type = self._classify_claim_type(sent_text)
                claims.append({
                    "text": sent_text,
                    "type": claim_type,
                    "has_numbers": self._contains_numbers(sent_text),
                    "has_quote": has_quote,
                    "entities": self._extract_entities(sent_text, sent),
                    "verifiability_score": self._calculate_verifiability(
                        sent_text, has_claim_verb, has_factual_pattern, has_quote
                    ),
                })

        claims.sort(key=lambda item: item["verifiability_score"], reverse=True)
        return claims

    def _classify_claim_type(self, text: str) -> str:
        """Classify the type of claim."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["accuse", "alleged", "blamed"]):
            return "accusation"
        if any(word in text_lower for word in ["deny", "denied", "reject"]):
            return "denial"
        if re.search(r"\d+\s*(people|casualties|deaths)", text, re.IGNORECASE):
            return "casualty_report"
        if re.search(r"\d+\s*percent|%", text):
            return "statistical"
        if any(word in text_lower for word in ["will", "plans to", "intends to"]):
            return "prediction"
        if '"' in text or "'" in text:
            return "quoted_statement"
        return "factual_claim"

    def _contains_numbers(self, text: str) -> bool:
        """Check if text contains numerical data."""
        return bool(re.search(r"\d+", text))

    def _extract_entities(self, text: str, sent=None) -> Dict:
        """Extract named entities from sentence text."""
        entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],
            "DATE": [],
            "NORP": [],
        }

        if sent is not None and hasattr(sent, "ents"):
            for ent in sent.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
        else:
            for match in re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text):
                if match in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}:
                    entities["DATE"].append(match)
                elif match in {"UN", "NATO", "EU", "WHO", "OPCW"}:
                    entities["ORG"].append(match)
                else:
                    entities["GPE"].append(match)

        return {key: values for key, values in entities.items() if values}

    def _calculate_verifiability(self, text: str, has_claim_verb: bool, has_factual_pattern: bool, has_quote: bool) -> float:
        """Calculate how verifiable a claim is (0-1 scale)."""
        score = 0.0

        if re.search(r"\d+", text):
            score += 0.3
        if re.search(r"\d{4}|January|February|March|April|May|June|July|August|September|October|November|December", text, re.IGNORECASE):
            score += 0.2

        doc = self._to_doc(text)
        ents = getattr(doc, "ents", [])
        if any(getattr(ent, "label_", None) in ["PERSON", "ORG", "GPE"] for ent in ents):
            score += 0.2
        elif re.search(r"\b[A-Z][a-z]+\b", text):
            score += 0.1

        if has_claim_verb:
            score += 0.2
        if has_factual_pattern:
            score += 0.1
        if has_quote:
            score += 0.05

        return min(score, 1.0)

    def extract_claims_from_articles(self, articles: List[Dict]) -> List[Dict]:
        """Extract claims from multiple articles."""
        print(f"\nExtracting claims from {len(articles)} articles...")

        analyzed_articles = []
        total_claims = 0

        for article in articles:
            title_claims = self.extract_claims_from_text(article.get("title", ""))
            desc_claims = self.extract_claims_from_text(article.get("description", ""))
            content_claims = self.extract_claims_from_text(article.get("content", ""))

            all_claims = title_claims + desc_claims + content_claims
            unique_claims = self._deduplicate_claims(all_claims)

            article_copy = article.copy()
            article_copy["extracted_claims"] = unique_claims
            article_copy["claim_count"] = len(unique_claims)

            total_claims += len(unique_claims)
            analyzed_articles.append(article_copy)

        average = total_claims / len(articles) if articles else 0.0
        print(f"Extracted {total_claims} total claims")
        print(f"Average {average:.1f} claims per article")
        return analyzed_articles

    def _deduplicate_claims(self, claims: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar claims."""
        if not claims:
            return []

        unique = []
        seen_texts = set()

        for claim in claims:
            text_normalized = claim["text"].lower().strip()
            is_duplicate = False

            for seen in seen_texts:
                words1 = set(text_normalized.split())
                words2 = set(seen.split())

                if len(words1) == 0 or len(words2) == 0:
                    continue

                overlap = len(words1 & words2) / max(len(words1), len(words2))
                if overlap > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(claim)
                seen_texts.add(text_normalized)

        return unique

    def get_top_claims(self, articles: List[Dict], n: int = 10) -> List[Dict]:
        """Get the top N most verifiable claims across all articles."""
        all_claims = []

        for article in articles:
            for claim in article.get("extracted_claims", []):
                all_claims.append({
                    "claim": claim,
                    "source_title": article.get("title", "Unknown"),
                    "source_url": article.get("url", ""),
                    "source": article.get("source", "Unknown"),
                })

        sorted_claims = sorted(
            all_claims,
            key=lambda item: item["claim"]["verifiability_score"],
            reverse=True,
        )
        return sorted_claims[:n]

    def _to_doc(self, text: str):
        """Create a spaCy doc when possible."""
        if self.nlp is not None:
            return self.nlp(text)
        if self.sentencizer is not None:
            return self.sentencizer(text)
        return text

    def _iter_sentences(self, doc, text: str):
        """Yield sentence-like objects from spaCy or regex fallback."""
        if hasattr(doc, "sents"):
            return doc.sents
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [_FallbackSentence(sentence) for sentence in sentences if sentence.strip()]

    def _sentence_has_claim_verb(self, sent) -> bool:
        """Check whether a sentence includes a claim verb."""
        if hasattr(sent, "__iter__") and not isinstance(sent, _FallbackSentence):
            return any(getattr(token, "lemma_", "").lower() in self.CLAIM_VERBS for token in sent)

        sent_text = sent.text.lower()
        return any(verb in sent_text for verb in self.CLAIM_VERBS)


class _FallbackSentence:
    """Minimal sentence wrapper used by the regex fallback."""

    def __init__(self, text: str):
        self.text = text
        self.ents = []


def main():
    """Example usage of ClaimExtractor."""
    print("=" * 70)
    print("STAGE 4: CLAIM EXTRACTION")
    print("=" * 70)

    input_file = "data/raw/news/test_articles.json"

    if not Path(input_file).exists():
        print(f"\nError: {input_file} not found")
        print("Please run Stage 1 first (news ingestion)")
        return

    print(f"\nLoading articles from: {input_file}")
    with open(input_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
        articles = data.get("articles", data)

    print(f"Loaded {len(articles)} articles")

    extractor = ClaimExtractor()
    analyzed_articles = extractor.extract_claims_from_articles(articles)

    print("\n" + "=" * 70)
    print("CLAIM STATISTICS")
    print("=" * 70)

    total_claims = sum(article["claim_count"] for article in analyzed_articles)
    print(f"\nTotal claims extracted: {total_claims}")
    print(f"Average claims per article: {total_claims / len(analyzed_articles):.1f}")

    top_claims = extractor.get_top_claims(analyzed_articles, n=5)

    print("\n" + "=" * 70)
    print("TOP 5 MOST VERIFIABLE CLAIMS")
    print("=" * 70)

    for i, item in enumerate(top_claims, 1):
        claim = item["claim"]
        print(f"\n[{i}] {claim['text']}")
        print(f"    Type: {claim['type']}")
        print(f"    Verifiability: {claim['verifiability_score']:.2f}")

    output_dir = Path("data/processed/claim_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted_claims.json"

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump({
            "total_articles": len(analyzed_articles),
            "total_claims": total_claims,
            "top_claims": top_claims,
            "articles": analyzed_articles,
        }, handle, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("CLAIM EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
