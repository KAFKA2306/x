import json
import tempfile
import unittest
from pathlib import Path

from src.input_readiness import load_configured_inputs
from src.models import AppConfig, FileConfig


class InputReadinessTests(unittest.TestCase):
    def make_config(self, root: Path, required_files=None) -> AppConfig:
        return AppConfig(
            input_file=str(root / "tweets.js"),
            output_dir=str(root / "out"),
            model_name="test",
            files=FileConfig(
                tweets=str(root / "tweets.js"),
                follower=str(root / "follower.js"),
                following=str(root / "following.js"),
                like=str(root / "like.js"),
                mute=str(root / "mute.js"),
            ),
            required_files=required_files or ["tweets"],
        )

    def write_archive(self, path: Path, items) -> None:
        path.write_text("window.YTD.test.part0 = " + json.dumps(items), encoding="utf-8")

    def status_for(self, state, name: str) -> str:
        return next(item.status for item in state.inputs if item.name == name)

    def test_required_tweets_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = load_configured_inputs(self.make_config(Path(tmp)))
        self.assertFalse(state.ready)
        self.assertEqual("missing-required", self.status_for(state, "tweets"))

    def test_present_empty_required_archive_is_valid_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_archive(root / "tweets.js", [])
            state = load_configured_inputs(self.make_config(root))
        self.assertTrue(state.ready)
        self.assertEqual("valid-empty", self.status_for(state, "tweets"))
        self.assertEqual([], state.data["tweets"])

    def test_malformed_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tweets.js").write_text("window.YTD.test.part0 = {", encoding="utf-8")
            state = load_configured_inputs(self.make_config(root))
        self.assertFalse(state.ready)
        self.assertEqual("invalid", self.status_for(state, "tweets"))

    def test_invalid_archive_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tweets.js").write_text("window.YTD.test.part0 = {}", encoding="utf-8")
            state = load_configured_inputs(self.make_config(root))
        self.assertFalse(state.ready)
        self.assertEqual("invalid", self.status_for(state, "tweets"))

    def test_valid_nonempty_archive_is_ready_and_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_archive(
                root / "tweets.js",
                [
                    {
                        "tweet": {
                            "created_at": "Mon Jan 01 00:00:00 +0000 2024",
                            "full_text": "hello",
                            "entities": {},
                        }
                    }
                ],
            )
            state = load_configured_inputs(self.make_config(root))
        self.assertTrue(state.ready)
        self.assertEqual("ready", self.status_for(state, "tweets"))
        self.assertEqual(1, len(state.data["tweets"]))

    def test_optional_missing_does_not_change_required_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_archive(root / "tweets.js", [])
            state = load_configured_inputs(self.make_config(root))
        self.assertTrue(state.ready)
        optional = [item for item in state.inputs if not item.required]
        self.assertTrue(optional)
        self.assertTrue(all(item.status == "optional-missing" for item in optional))


if __name__ == "__main__":
    unittest.main()
