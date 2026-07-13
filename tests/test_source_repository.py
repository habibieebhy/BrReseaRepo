import tempfile
import unittest
from pathlib import Path

from runtime.sources.repository import SourceRepository


class SourceRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.original_path = SourceRepository._path
        self.directory = tempfile.TemporaryDirectory()
        SourceRepository._path = Path(self.directory.name) / "sources.json"

    def tearDown(self):
        SourceRepository._path = self.original_path
        self.directory.cleanup()

    def test_create_update_delete_source(self):
        created = SourceRepository.create({"name": "Docs", "tenant_id": "acme"})
        self.assertEqual(SourceRepository.get(created["id"])["name"], "Docs")
        updated = SourceRepository.update(created["id"], {"name": "Product Docs"})
        self.assertEqual(updated["name"], "Product Docs")
        self.assertTrue(SourceRepository.delete(created["id"]))
        self.assertIsNone(SourceRepository.get(created["id"]))

    def test_tenant_filter(self):
        SourceRepository.create({"name": "A", "tenant_id": "one"})
        SourceRepository.create({"name": "B", "tenant_id": "two"})
        self.assertEqual(len(SourceRepository.list("one")), 1)


if __name__ == "__main__":
    unittest.main()
