"""
Narrative Synthesis Module - Stage 5.
Generates evidence-based counter-narratives for verified claims.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .evidence_compiler import EvidenceCompiler
from .llm_client import LLMClient, LLMGenerationError
from .tone_adjuster import ToneAdjuster


class NarrativeGenerator:
    """Generate counter-narratives based on fact-checking results."""

    TEMPLATES = {
        "accusation": {
            "intro": "Regarding the claim that {claim}, our analysis shows:",
            "evidence_section": "Evidence from {source_count} sources indicates:",
            "conclusion": "Conclusion: {verdict}",
        },
        "statistical": {
            "intro": "The statistical claim states: {claim}",
            "evidence_section": "Verification against {source_count} authoritative sources:",
            "conclusion": "Assessment: {verdict}",
        },
        "casualty_report": {
            "intro": "Concerning casualty reports claiming {claim}:",
            "evidence_section": "Cross-referenced with {source_count} independent sources:",
            "conclusion": "Verified status: {verdict}",
        },
        "default": {
            "intro": "Claim: {claim}",
            "evidence_section": "After reviewing {source_count} sources:",
            "conclusion": "Finding: {verdict}",
        },
    }

    def __init__(self, *, use_llm: bool = False, llm_client: LLMClient | None = None):
        """Initialize narrative generator."""
        print("Initializing narrative generator...")
        self.compiler = EvidenceCompiler()
        self.tone_adjuster = ToneAdjuster()
        self.use_llm = use_llm
        self.llm_client = llm_client

    def generate_verdict(self, verification_status: str, credibility_score: float) -> str:
        """Generate a verdict statement based on verification results."""
        if verification_status == "likely_true":
            if credibility_score > 0.9:
                return "This claim is strongly supported by available evidence"
            return "This claim appears credible based on current evidence"

        if verification_status == "disputed":
            return "This claim is disputed by multiple credible sources and requires correction"

        return "This claim requires additional verification from independent sources"

    def generate_evidence_summary(self, evidence: List[Dict]) -> List[str]:
        """Create fallback bullet points summarizing evidence."""
        summaries = []
        for index, item in enumerate(evidence[:3], 1):
            source = item.get("source", "Unknown source")
            credibility = item.get("credibility_score", 0)
            snippet = item.get("snippet", "No description available")
            summaries.append(f"[{index}] {source} (credibility: {credibility:.2f}): {snippet[:100]}...")
        return summaries

    def generate_counter_narrative(self, verified_claim: Dict, tone: str = "analytical") -> Dict:
        """Generate a complete counter-narrative for a verified claim."""
        claim_text = verified_claim.get("claim", "")
        claim_type = verified_claim.get("claim_type", "default")
        status = verified_claim.get("verification_status", "needs_verification")
        credibility = verified_claim.get("credibility_score", 0)
        evidence = verified_claim.get("evidence", [])

        template = self.TEMPLATES.get(claim_type, self.TEMPLATES["default"])
        intro = template["intro"].format(claim=claim_text[:100])
        compiled = self.compiler.compile(verified_claim)
        evidence_header = template["evidence_section"].format(source_count=compiled["source_count"])
        evidence_bullets = compiled["bullet_points"] or self.generate_evidence_summary(evidence)
        verdict = self.generate_verdict(status, credibility)
        conclusion = template["conclusion"].format(verdict=verdict)
        generation_backend = "template"
        llm_error = ""

        if self.use_llm:
            try:
                narrative_text = self._generate_llm_counter_narrative(
                    verified_claim=verified_claim,
                    compiled=compiled,
                    tone=tone,
                    verdict=verdict,
                )
                generation_backend = "llm"
            except LLMGenerationError as exc:
                llm_error = str(exc)
                narrative_text = self._generate_template_text(
                    intro=intro,
                    evidence_header=evidence_header,
                    evidence_bullets=evidence_bullets,
                    conclusion=conclusion,
                    tone=tone,
                )
                generation_backend = "template_fallback"
        else:
            narrative_text = self._generate_template_text(
                intro=intro,
                evidence_header=evidence_header,
                evidence_bullets=evidence_bullets,
                conclusion=conclusion,
                tone=tone,
            )

        result = {
            "original_claim": claim_text,
            "claim_type": claim_type,
            "verification_status": status,
            "credibility_score": credibility,
            "counter_narrative": narrative_text,
            "evidence_count": len(evidence),
            "generated_at": datetime.now().isoformat(),
            "confidence": "high" if credibility > 0.8 else "medium" if credibility > 0.6 else "low",
            "tone": tone,
            "bibliography": compiled["bibliography"],
            "generation_backend": generation_backend,
        }
        if self.llm_client is not None and self.llm_client.model:
            result["llm_model"] = self.llm_client.model
            result["llm_provider"] = self.llm_client.provider
        if llm_error:
            result["llm_error"] = llm_error
        return result

    def _generate_template_text(
        self,
        *,
        intro: str,
        evidence_header: str,
        evidence_bullets: List[str],
        conclusion: str,
        tone: str,
    ) -> str:
        narrative_parts = [
            intro,
            "",
            evidence_header,
            *evidence_bullets,
            "",
            conclusion,
        ]
        return self.tone_adjuster.adjust("\n".join(narrative_parts), tone=tone)

    def _generate_llm_counter_narrative(
        self,
        *,
        verified_claim: Dict,
        compiled: Dict,
        tone: str,
        verdict: str,
    ) -> str:
        if self.llm_client is None:
            raise LLMGenerationError("LLM client is not configured.")

        system_prompt = (
            "You are a careful geopolitical fact-checking analyst. Generate concise "
            "counter-narratives only from the supplied claim and evidence. Do not add "
            "new facts, do not speculate, and do not use manipulative language. "
            "Acknowledge uncertainty when verification status is needs_verification. "
            "Use bracket citations like [1] that correspond to the supplied evidence."
        )
        user_prompt = self._build_llm_prompt(
            verified_claim=verified_claim,
            compiled=compiled,
            tone=tone,
            verdict=verdict,
        )
        generated = self.llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        return self.tone_adjuster.adjust(generated, tone=tone)

    def _build_llm_prompt(self, *, verified_claim: Dict, compiled: Dict, tone: str, verdict: str) -> str:
        evidence_lines = compiled["bullet_points"] or self.generate_evidence_summary(verified_claim.get("evidence", []))
        bibliography = compiled["bibliography"] or []
        return "\n".join(
            [
                f"Tone: {tone}",
                f"Claim: {verified_claim.get('claim', '')}",
                f"Claim type: {verified_claim.get('claim_type', 'unknown')}",
                f"Verification status: {verified_claim.get('verification_status', 'needs_verification')}",
                f"Credibility score: {verified_claim.get('credibility_score', 0)}",
                f"Verdict to preserve: {verdict}",
                "",
                "Evidence:",
                *evidence_lines,
                "",
                "Bibliography:",
                *bibliography,
                "",
                "Write a 120-180 word counter-narrative with: context, evidence-based assessment, and a clear uncertainty note when needed.",
            ]
        )

    def generate_multiple_narratives(self, verified_claims: List[Dict], tone: str = "analytical") -> List[Dict]:
        """Generate counter-narratives for multiple claims."""
        print(f"\nGenerating counter-narratives for {len(verified_claims)} claims...")
        narratives = []

        for index, claim in enumerate(verified_claims, 1):
            print(f"[{index}/{len(verified_claims)}] Generating narrative...")
            narratives.append(self.generate_counter_narrative(claim, tone=tone))

        print(f"Generated {len(narratives)} counter-narratives")
        return narratives

    def create_summary_report(self, narratives: List[Dict]) -> str:
        """Create a human-readable summary report."""
        report_lines = [
            "=" * 70,
            "COUNTER-NARRATIVE SYNTHESIS REPORT",
            "=" * 70,
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total narratives: {len(narratives)}",
            "",
        ]

        high_conf = sum(1 for narrative in narratives if narrative["confidence"] == "high")
        disputed = sum(1 for narrative in narratives if narrative["verification_status"] == "disputed")
        backend_counts = {}
        for narrative in narratives:
            backend = narrative.get("generation_backend", "template")
            backend_counts[backend] = backend_counts.get(backend, 0) + 1

        report_lines.extend([
            "SUMMARY:",
            f"  High confidence narratives: {high_conf}",
            f"  Disputed claims addressed: {disputed}",
            f"  Generation backends: {backend_counts}",
            "",
            "=" * 70,
            "COUNTER-NARRATIVES",
            "=" * 70,
        ])

        for index, narrative in enumerate(narratives, 1):
            report_lines.extend([
                "",
                f"[{index}] " + "=" * 65,
                f"CLAIM: {narrative['original_claim'][:80]}...",
                f"STATUS: {narrative['verification_status'].upper()}",
                f"CONFIDENCE: {narrative['confidence'].upper()}",
                f"TONE: {narrative['tone'].upper()}",
                "",
                narrative["counter_narrative"],
                "",
                "Sources:",
                *[f"  {line}" for line in narrative.get("bibliography", [])],
                "",
            ])

        return "\n".join(report_lines)


def main():
    """Generate counter-narratives from verified claims."""
    print("=" * 70)
    print("STAGE 5: NARRATIVE SYNTHESIS")
    print("=" * 70)

    input_file = "data/processed/fact_verification/verified_claims.json"

    if not Path(input_file).exists():
        print(f"\nError: {input_file} not found")
        print("Please run Stage 4 first:")
        print("  python test_claim_verification.py")
        return

    print(f"\nLoading verified claims from: {input_file}")
    with open(input_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    verified_claims = data.get("verified_claims", [])
    if not verified_claims:
        print("No verified claims found")
        return

    print(f"Loaded {len(verified_claims)} verified claims")
    generator = NarrativeGenerator()
    narratives = generator.generate_multiple_narratives(verified_claims)
    report_text = generator.create_summary_report(narratives)

    output_dir = Path("data/processed/narrative_synthesis")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "counter_narratives.json"
    with open(json_file, "w", encoding="utf-8") as handle:
        json.dump({
            "total_narratives": len(narratives),
            "generated_at": datetime.now().isoformat(),
            "narratives": narratives,
        }, handle, indent=2, ensure_ascii=False)

    report_file = output_dir / "COUNTER_NARRATIVE_REPORT.txt"
    with open(report_file, "w", encoding="utf-8") as handle:
        handle.write(report_text)

    print(f"JSON results saved to: {json_file}")
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()
