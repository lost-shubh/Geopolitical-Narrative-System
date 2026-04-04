"""
Offline-friendly social reaction ingestion.
Uses the bundled mock dataset when live APIs are unavailable.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class SocialIngestor:
    """Load or generate social reaction datasets."""

    def __init__(self, data_dir: str = "data/raw/social"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_comments(self, filepath: str | Path) -> List[Dict]:
        """Load comments from a JSON file."""
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and "comments" in data:
            return data["comments"]
        if isinstance(data, list):
            return data
        return []

    def save_comments(self, comments: List[Dict], filename: str = "mock_social_comments.json", metadata: Optional[Dict] = None) -> str:
        """Persist comments using the project JSON format."""
        output_path = self.data_dir / filename
        payload = metadata.copy() if metadata else {}
        payload.update({
            "total_comments": len(comments),
            "comments": comments,
        })
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        return str(output_path)

    def load_or_generate(self, filename: str = "mock_social_comments.json") -> str:
        """Return an existing dataset or create one using the bundled generator."""
        output_path = self.data_dir / filename
        if output_path.exists():
            return str(output_path)

        import create_mock_data

        return str(create_mock_data.create_mock_social_dataset())
