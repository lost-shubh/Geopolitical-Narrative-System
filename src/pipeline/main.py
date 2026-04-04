"""
End-to-end five-stage pipeline entrypoint.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

from src.pipeline.stage1_content_extraction import run_stage as run_stage1
from src.pipeline.stage2_reaction_analysis import run_stage as run_stage2
from src.pipeline.stage3_reaction_analysis import run_stage as run_stage3
from src.pipeline.stage4_fact_discovery import run_stage as run_stage4
from src.pipeline.stage5_narrative_synthesis import run_stage as run_stage5
from src.utils.api_clients import load_pipeline_config
from src.utils.database import PipelineDatabase


def run_pipeline(
    *,
    topic: str | None = None,
    days_back: int | None = None,
    max_articles: int | None = None,
    use_existing_data: bool | None = None,
    offline_mode: bool | None = None,
    tone: str | None = None,
) -> Dict:
    """Run the full five-stage pipeline."""
    load_dotenv()
    pipeline_config = load_pipeline_config()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    database = PipelineDatabase()

    stage1_result = run_stage1(
        query=topic or pipeline_config["topic"],
        days_back=days_back,
        max_articles=max_articles,
        use_existing_data=use_existing_data,
        offline_mode=offline_mode,
    )
    database.record_stage(run_id, "stage1", "completed", {"processed_file": stage1_result["processed_file"]})

    stage2_result = run_stage2(stage1_result=stage1_result)
    database.record_stage(run_id, "stage2", "completed", {"processed_file": stage2_result["processed_file"]})

    stage3_result = run_stage3(stage1_result=stage1_result, stage2_result=stage2_result)
    database.record_stage(run_id, "stage3", "completed", {"news_file": stage3_result["news_file"], "social_file": stage3_result["social_file"]})

    stage4_result = run_stage4(stage1_result=stage1_result)
    database.record_stage(run_id, "stage4", "completed", {"verified_file": stage4_result["verified_file"]})

    stage5_result = run_stage5(stage4_result=stage4_result, stage3_result=stage3_result, tone=tone)
    database.record_stage(run_id, "stage5", "completed", {"report_file": stage5_result["final_report"]})

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
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the full geopolitical narrative pipeline.")
    parser.add_argument("--topic", help="News query override")
    parser.add_argument("--days", type=int, help="Days back to search")
    parser.add_argument("--max-articles", type=int, help="Maximum article count")
    parser.add_argument("--offline", action="store_true", help="Use only local project data")
    parser.add_argument("--no-existing-data", action="store_true", help="Prefer fresh ingestion over existing files")
    parser.add_argument("--tone", choices=["analytical", "public", "policy"], help="Narrative tone")
    return parser


def cli_main() -> Dict:
    args = build_parser().parse_args()
    result = run_pipeline(
        topic=args.topic,
        days_back=args.days,
        max_articles=args.max_articles,
        use_existing_data=not args.no_existing_data,
        offline_mode=args.offline,
        tone=args.tone,
    )
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Run summary: {result['summary_file']}")
    print(f"Final report: {result['stage5']['final_report']}")
    return result


if __name__ == "__main__":
    cli_main()
