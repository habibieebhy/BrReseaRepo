import unittest

from core.exceptions import ValidationError
from core.plugin_loader import PLUGIN_STAGES, PluginRegistry, PluginSpec, registry


class PluginRegistryTests(unittest.TestCase):
    def test_defaults_resolve_for_every_pipeline_stage(self):
        selection = registry.validate_selection({})
        self.assertEqual(set(selection), set(PLUGIN_STAGES))
        self.assertEqual(selection["parser"], "docling")

    def test_per_job_override_is_preserved(self):
        selection = registry.validate_selection({"embedding": "sentence-transformers"})
        self.assertEqual(selection["embedding"], "sentence-transformers")

    def test_unknown_plugin_is_rejected_before_dispatch(self):
        with self.assertRaises(ValidationError):
            registry.validate_selection({"parser": "made-up"})

    def test_model_profile_controls_remote_code_and_dimensions(self):
        profile = registry.resolve_model("sentence-transformers", "nomic-ai/nomic-embed-text-v1.5")
        self.assertTrue(profile.trust_remote_code)
        self.assertEqual(profile.dimensions, 768)
        self.assertTrue(profile.revision)

    def test_unapproved_model_is_rejected(self):
        with self.assertRaises(ValidationError):
            registry.resolve_model("sentence-transformers", "unknown/potentially-dangerous-model")

    def test_duplicate_default_is_rejected(self):
        candidate = PluginRegistry()
        candidate.register(PluginSpec("one", "parser", "One", "1", "x:y", default=True))
        with self.assertRaises(ValidationError):
            candidate.register(PluginSpec("two", "parser", "Two", "1", "x:y", default=True))


if __name__ == "__main__":
    unittest.main()
