"""
Stage 5: counter-narrative generation and reporting.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.synthesis.narrative_generator import NarrativeGenerator
from src.synthesis.llm_client import LLMClient
from src.utils.api_clients import load_pipeline_config


def _load_stage_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_final_report(report_path: Path, stage3_result: Dict | None, stage4_result: Dict, narratives: list[Dict], tone: str) -> None:
    news_results = stage3_result.get("news_results", {}) if stage3_result else {}
    social_results = stage3_result.get("social_results", {}) if stage3_result else {}
    verified_payload = stage4_result["verified_payload"]

    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write("=" * 70 + "\n")
        handle.write("GEOPOLITICAL NARRATIVE INTELLIGENCE SYSTEM\n")
        handle.write("FINAL PIPELINE REPORT\n")
        handle.write("=" * 70 + "\n\n")
        handle.write(f"Tone: {tone}\n")
        handle.write(f"Verified claims: {verified_payload['total_verified']}\n")
        handle.write(f"Generated narratives: {len(narratives)}\n\n")
        backend_counts = {}
        for narrative in narratives:
            backend = narrative.get("generation_backend", "template")
            backend_counts[backend] = backend_counts.get(backend, 0) + 1
        handle.write(f"Generation backends: {backend_counts}\n\n")

        if news_results:
            sent = news_results["sentiment_statistics"]
            emo = news_results["emotion_statistics"]
            handle.write("NEWS ANALYSIS\n")
            handle.write("-" * 70 + "\n")
            handle.write(f"Articles analyzed: {sent['total_analyzed']}\n")
            handle.write(f"Negative coverage: {sent['negative_percent']}%\n")
            handle.write(f"Dominant emotion: {emo['most_common_emotion']}\n\n")

        if social_results:
            polarization = social_results["polarization"]
            engagement = social_results["engagement"]
            handle.write("PUBLIC REACTION ANALYSIS\n")
            handle.write("-" * 70 + "\n")
            handle.write(f"Comments analyzed: {social_results['total_comments']}\n")
            handle.write(f"Polarization level: {polarization['level']} ({polarization['score']})\n")
            handle.write(f"Virality score: {engagement['virality_score']}\n\n")

        handle.write("VERIFICATION SUMMARY\n")
        handle.write("-" * 70 + "\n")
        handle.write(f"Average credibility: {verified_payload['statistics']['average_credibility']}\n")
        handle.write(f"Disputed claims: {verified_payload['statistics']['disputed_count']}\n\n")

        handle.write("COUNTER-NARRATIVES\n")
        handle.write("-" * 70 + "\n")
        for index, narrative in enumerate(narratives[:5], start=1):
            handle.write(f"[{index}] {narrative['original_claim'][:120]}\n")
            handle.write(f"Status: {narrative['verification_status']} | Confidence: {narrative['confidence']}\n")
            handle.write(narrative["counter_narrative"] + "\n")
            if narrative.get("bibliography"):
                handle.write("Sources:\n")
                for line in narrative["bibliography"]:
                    handle.write(f"  {line}\n")
            handle.write("\n")


def run_stage(
    *,
    stage4_result: Dict | None = None,
    stage3_result: Dict | None = None,
    tone: str | None = None,
    use_llm: bool | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_api_base: str | None = None,
) -> Dict:
    """Generate counter-narratives and stage-5 reports."""
    pipeline_config = load_pipeline_config()
    tone = tone or pipeline_config["default_tone"]
    use_llm = bool(pipeline_config.get("llm_enabled", False)) if use_llm is None else use_llm

    if stage4_result is None:
        stage4_result = {
            "verified_payload": _load_stage_json("data/processed/stage4_fact_discovery/verified_claims.json"),
        }
    if stage3_result is None:
        try:
            stage3_result = {
                "news_results": _load_stage_json("data/processed/stage3_reaction_analysis/news_analysis.json"),
                "social_results": _load_stage_json("data/processed/stage3_reaction_analysis/social_analysis.json"),
            }
        except FileNotFoundError:
            stage3_result = None

    verified_claims = stage4_result["verified_payload"].get("verified_claims", [])
    llm_client = None
    if use_llm:
        llm_client = LLMClient.from_config(
            provider=llm_provider,
            model=llm_model,
            api_base=llm_api_base,
        )
    generator = NarrativeGenerator(use_llm=use_llm, llm_client=llm_client)
    narratives = generator.generate_multiple_narratives(verified_claims, tone=tone)
    stage_report = generator.create_summary_report(narratives)

    output_dir = Path("data/processed/stage5_narrative_synthesis")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_file = output_dir / "counter_narratives.json"
    report_file = output_dir / "COUNTER_NARRATIVE_REPORT.txt"
    final_report = Path("data/processed/pipeline_results/FINAL_REPORT.txt")
    final_report.parent.mkdir(parents=True, exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as handle:
        json.dump({
            "total_narratives": len(narratives),
            "tone": tone,
            "llm_enabled": use_llm,
            "narratives": narratives,
        }, handle, indent=2, ensure_ascii=False)
    with open(report_file, "w", encoding="utf-8") as handle:
        handle.write(stage_report)

    _write_final_report(final_report, stage3_result, stage4_result, narratives, tone)

    legacy_dir = Path("data/processed/narrative_synthesis")
    legacy_dir.mkdir(parents=True, exist_ok=True)
    with open(legacy_dir / "counter_narratives.json", "w", encoding="utf-8") as handle:
        json.dump({
            "total_narratives": len(narratives),
            "tone": tone,
            "llm_enabled": use_llm,
            "narratives": narratives,
        }, handle, indent=2, ensure_ascii=False)
    with open(legacy_dir / "COUNTER_NARRATIVE_REPORT.txt", "w", encoding="utf-8") as handle:
        handle.write(stage_report)

    return {
        "json_file": str(json_file),
        "report_file": str(report_file),
        "final_report": str(final_report),
        "narratives": narratives,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage 5 narrative synthesis.")
    parser.add_argument("--tone", default=None, help="Narrative tone: analytical, public, policy")
    parser.add_argument("--llm", action="store_true", help="Use optional LLM generation with template fallback")
    parser.add_argument("--llm-provider", help="LLM provider: openai_responses or openai_chat")
    parser.add_argument("--llm-model", help="LLM model override")
    parser.add_argument("--llm-api-base", help="OpenAI-compatible API base URL")
    return parser


def cli_main() -> Dict:
    args = build_parser().parse_args()
    result = run_stage(
        tone=args.tone,
        use_llm=args.llm,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_api_base=args.llm_api_base,
    )
    print("Stage 5 complete.")
    print(f"Narratives file: {result['json_file']}")
    print(f"Final report: {result['final_report']}")
    return result


if __name__ == "__main__":
    cli_main()
