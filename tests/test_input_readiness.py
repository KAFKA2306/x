import tempfile
import unittest
from pathlib import Path

from src.input_readiness import evaluate_inputs, required_inputs_ready
from src.models import AppConfig, FileConfig


class InputReadinessTest(unittest.TestCase):
    def config(self, root: Path) -> AppConfig:
        files = FileConfig(
            tweets=str(root / "tweets.js"),
            follower=str(root / "follower.js"),
            following=str(root / "following.js"),
            like=str(root / "like.js"),
            mute=str(root / "mute.js"),
        )
        return AppConfig(input_file="unused", output_dir="unused", model_name="unused", files=files)

    def test_required_tweets_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            states = evaluate_inputs(self.config(Path(tmp)))
            self.assertEqual(states["tweets"].status, "missing_required")
            self.assertFalse(required_inputs_ready(states))

    def test_present_empty_tweets_is_valid_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tweets.js").write_text("[]", encoding="utf-8")
            states = evaluate_inputs(self.config(root))
            self.assertEqual(states["tweets"].status, "valid_empty")
            self.assertTrue(required_inputs_ready(states))

    def test_malformed_required_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tweets.js").write_text("not-json", encoding="utf-8")
            states = evaluate_inputs(self.config(root))
            self.assertEqual(states["tweets"].status, "invalid")
            self.assertFalse(required_inputs_ready(states))

    def test_valid_nonempty_tweets_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = (
                '[{"tweet":{"created_at":"Mon Jan 01 00:00:00 +0000 2024",'
                '"full_text":"hello","entities":{}}}]'
            )
            (root / "tweets.js").write_text(payload, encoding="utf-8")
            states = evaluate_inputs(self.config(root))
            self.assertEqual(states["tweets"].status, "ready")
            self.assertEqual(len(states["tweets"].data), 1)
            self.assertTrue(required_inputs_ready(states))

    def test_optional_missing_does_not_change_required_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tweets.js").write_text("[]", encoding="utf-8")
            states = evaluate_inputs(self.config(root))
            self.assertEqual(states["like"].status, "optional_missing")
            self.assertTrue(required_inputs_ready(states))


if __name__ == "__main__":
    unittest.main()
