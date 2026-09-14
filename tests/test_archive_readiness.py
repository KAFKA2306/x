import json
import tempfile
import unittest
from pathlib import Path

from src.loader import ArchiveInputStatus, load_archive_inputs
from src.models import AppConfig, ArchiveInputPolicy, FileConfig


class ArchiveReadinessTests(unittest.TestCase):
    def make_config(self, root: Path) -> AppConfig:
        return AppConfig(
            input_file=str(root / "tweets.js"),
            output_dir=str(root / "output"),
            model_name="test",
            files=FileConfig(
                tweets=str(root / "tweets.js"),
                follower=str(root / "follower.js"),
                following=str(root / "following.js"),
                like=str(root / "like.js"),
                mute=str(root / "mute.js"),
            ),
            archive_inputs=ArchiveInputPolicy(
                required=["tweets"],
                optional=["follower", "following", "like", "mute"],
            ),
        )

    def write(self, path: Path, payload) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_required_tweets_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = load_archive_inputs(self.make_config(Path(tmp)))
            self.assertFalse(result.analysis_ready)
            self.assertEqual(result.readiness["tweets"].status, ArchiveInputStatus.MISSING_REQUIRED)

    def test_present_empty_required_archive_is_valid_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "tweets.js", [])
            result = load_archive_inputs(self.make_config(root))
            self.assertTrue(result.analysis_ready)
            self.assertEqual(result.readiness["tweets"].status, ArchiveInputStatus.VALID_EMPTY)
            self.assertEqual(result.tweets, [])

    def test_malformed_archive_is_invalid_and_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tweets.js").write_text("not-json", encoding="utf-8")
            result = load_archive_inputs(self.make_config(root))
            self.assertFalse(result.analysis_ready)
            self.assertEqual(result.readiness["tweets"].status, ArchiveInputStatus.INVALID)

    def test_valid_non_empty_archive_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root / "tweets.js",
                [
                    {
                        "tweet": {
                            "created_at": "Mon Sep 14 00:00:00 +0000 2026",
                            "full_text": "hello",
                            "entities": {"user_mentions": [], "hashtags": [], "urls": []},
                            "favorite_count": "1",
                            "retweet_count": "0",
                        }
                    }
                ],
            )
            result = load_archive_inputs(self.make_config(root))
            self.assertTrue(result.analysis_ready)
            self.assertEqual(result.readiness["tweets"].status, ArchiveInputStatus.READY)
            self.assertEqual(len(result.tweets), 1)

    def test_optional_missing_is_explicit_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "tweets.js", [])
            config = self.make_config(root)
            first = load_archive_inputs(config)
            second = load_archive_inputs(config)
            self.assertTrue(first.analysis_ready)
            self.assertEqual(first.readiness["like"].status, ArchiveInputStatus.OPTIONAL_MISSING)
            self.assertEqual(first.readiness, second.readiness)


if __name__ == "__main__":
    unittest.main()
