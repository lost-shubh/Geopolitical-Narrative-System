"""
End-to-end five-stage pipeline entrypoint.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from src.pipeline.stage1_content_extraction import run_stage as run_stage1
from src.pipeline.stage2_reaction_analysis import run_stage as run_stage2
from src.pipeline.stage3_reaction_analysis import run_stage as run_stage3
from src.pipeline.stage4_fact_discovery import run_stage as run_stage4
from src.pipeline.stage5_narrative_synthesis import run_stage as run_stage5
from src.utils.api_clients import load_pipeline_config
from src.utils.database import PipelineDatabase


def _print_live_section(title: str, lines: list[str]) -> None:
    """Print a compact live status block to stdout."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    for line in lines:
        print(line)


def run_pipeline(
    *,
    topic: str | None = None,
    days_back: int | None = None,
    max_articles: int | None = None,
    use_existing_data: bool | None = None,
    offline_mode: bool | None = None,
    strict_live: bool | None = None,
    tone: str | None = None,
    comments_file: str | None = None,
    use_llm: bool | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_api_base: str | None = None,
    live_output: bool = False,
) -> Dict:
    """Run the full five-stage pipeline."""
    load_dotenv()
    pipeline_config = load_pipeline_config()
    if strict_live is None:
        strict_live = False if offline_mode else pipeline_config.get("realtime_only", False)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    database = PipelineDatabase()

    stage1_result = run_stage1(
        query=topic or pipeline_config["topic"],
        days_back=days_back,
        max_articles=max_articles,
        use_existing_data=use_existing_data,
        offline_mode=offline_mode,
        strict_live=strict_live,
    )
    database.record_stage(run_id, "stage1", "completed", {"processed_file": stage1_result["processed_file"]})
    if live_output:
        _print_live_section("STAGE 1 COMPLETE", [
            f"Articles processed: {stage1_result['article_count']}",
            f"Topics: {stage1_result['topic_distribution']}",
            f"Saved: {stage1_result['processed_file']}",
        ])

    stage2_result = run_stage2(
        stage1_result=stage1_result,
        comments_file=comments_file,
    )
    database.record_stage(run_id, "stage2", "completed", {"processed_file": stage2_result["processed_file"]})
    if live_output:
        _print_live_section("STAGE 2 COMPLETE", [
            f"Comments collected: {stage2_result['comment_count']}",
            f"Reaction source: {stage2_result['reaction_source']}",
            f"Platforms: {stage2_result['platform_distribution']}",
            f"Saved: {stage2_result['processed_file']}",
        ])

    stage3_result = run_stage3(stage1_result=stage1_result, stage2_result=stage2_result)
    database.record_stage(run_id, "stage3", "completed", {"news_file": stage3_result["news_file"], "social_file": stage3_result["social_file"]})
    if live_output:
        news_stats = stage3_result["news_results"]["sentiment_statistics"]
        social_stats = stage3_result["social_results"]
        _print_live_section("STAGE 3 COMPLETE", [
            f"News articles analyzed: {news_stats['total_analyzed']}",
            f"News negative: {news_stats['negative_percent']}%",
            f"Comments analyzed: {social_stats['total_comments']}",
            f"Polarization: {social_stats['polarization']['level']} ({social_stats['polarization']['score']})",
        ])

    stage4_result = run_stage4(stage1_result=stage1_result)
    database.record_stage(run_id, "stage4", "completed", {"verified_file": stage4_result["verified_file"]})
    if live_output:
        verification = stage4_result["verified_payload"]["statistics"]
        _print_live_section("STAGE 4 COMPLETE", [
            f"Claims verified: {verification['total_verified']}",
            f"Average credibility: {verification['average_credibility']}",
            f"Disputed claims: {verification['disputed_count']}",
        ])

    stage5_result = run_stage5(
        stage4_result=stage4_result,
        stage3_result=stage3_result,
        tone=tone,
        use_llm=use_llm,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_base=llm_api_base,
    )
    database.record_stage(run_id, "stage5", "completed", {"report_file": stage5_result["final_report"]})
    if live_output:
        _print_live_section("STAGE 5 COMPLETE", [
            f"Narratives generated: {len(stage5_result['narratives'])}",
            f"Final report: {stage5_result['final_report']}",
        ])

    output_dir = Path("data/processed/pipeline_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_file = output_dir / "pipeline_run_summary.json"
    summary = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "stage1": {
            "article_count": stage1_result["article_count"],
            "processed_file": stage1_result["processed_file"],
        },
        "stage2": {
            "comment_count": stage2_result["comment_count"],
            "reaction_source": stage2_result["reaction_source"],
            "processed_file": stage2_result["processed_file"],
        },
        "stage3": {
            "news_file": stage3_result["news_file"],
            "social_file": stage3_result["social_file"],
        },
        "stage4": {
            "claims_file": stage4_result["claims_file"],
            "verified_file": stage4_result["verified_file"],
        },
        "stage5": {
            "narratives_file": stage5_result["json_file"],
            "final_report": stage5_result["final_report"],
        },
    }
    with open(summary_file, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    summary["summary_file"] = str(summary_file)

    if live_output:
        final_report_path = Path(stage5_result["final_report"])
        if final_report_path.exists():
            print("\n" + "=" * 70)
            print("FINAL REPORT")
            print("=" * 70)
            with open(final_report_path, "r", encoding="utf-8") as handle:
                print(handle.read())

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the full geopolitical narrative pipeline.")
    parser.add_argument("--topic", help="News query override")
    parser.add_argument("--days", type=int, help="Days back to search")
    parser.add_argument("--max-articles", type=int, help="Maximum article count")
    parser.add_argument("--offline", action="store_true", help="Use only local project data")
    parser.add_argument(
        "--use-existing-data",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Use cached news data when available; defaults to config value when omitted",
    )
    parser.add_argument("--strict-live", action="store_true", help="Require live NewsAPI fetch for Stage 1")
    parser.add_argument("--no-strict-live", action="store_true", help="Disable strict live mode")
    parser.add_argument("--tone", choices=["analytical", "public", "policy"], help="Narrative tone")
    parser.add_argument("--comments-file", help="Optional JSON export of real social comments for Stage 2")
    parser.add_argument("--llm", action="store_true", help="Use optional LLM narrative synthesis in Stage 5")
    parser.add_argument("--llm-provider", help="LLM provider: openai_responses or openai_chat")
    parser.add_argument("--llm-model", help="LLM model override")
    parser.add_argument("--llm-api-base", help="OpenAI-compatible API base URL")
    parser.add_argument("--live", action="store_true", help="Print stage summaries and the final report in the terminal")
    return parser


def cli_main() -> Dict:
    args = build_parser().parse_args()
    strict_live = None
    if args.strict_live and args.no_strict_live:
        raise SystemExit("Choose only one of --strict-live or --no-strict-live.")
    if args.strict_live:
        strict_live = True
    elif args.no_strict_live:
        strict_live = False

    result = run_pipeline(
        topic=args.topic,
        days_back=args.days,
        max_articles=args.max_articles,
        use_existing_data=args.use_existing_data,
        offline_mode=args.offline,
        strict_live=strict_live,
        tone=args.tone,
        comments_file=args.comments_file,
        use_llm=args.llm,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_api_base=args.llm_api_base,
        live_output=args.live,
    )
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Run summary: {result['summary_file']}")
    print(f"Final report: {result['stage5']['final_report']}")
    return result


if __name__ == "__main__":
    cli_main()
