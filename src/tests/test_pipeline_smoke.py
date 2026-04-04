"""Smoke test for the offline pipeline path."""

from pathlib import Path

from src.pipeline.main import run_pipeline


def test_offline_pipeline_produces_summary_and_report():
    result = run_pipeline(use_existing_data=True, offline_mode=True, tone="analytical")

    assert Path(result["summary_file"]).exists()
    assert Path(result["stage5"]["final_report"]).exists()
