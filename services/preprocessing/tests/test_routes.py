"""Preprocessing API regressions, without downloading tokenizer data."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# The production chunker downloads punkt_tab at import time. These API tests
# supply known sentence boundaries instead, so they can run without network.
with patch("nltk.download"):
    from services.preprocessing.app import chunker, routes


class PreprocessRouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(routes.router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.sentences = [
            "First short sentence.",
            "Second short sentence.",
            "Third short sentence.",
            "Fourth short sentence.",
        ]
        self.payload = {
            "doc_id": "doc-123",
            "source_type": "text",
            "filename": "example.txt",
            "text_content": " ".join(self.sentences),
            "extra_metadata": {"author": "Example"},
        }
        for patcher in (
            patch.object(routes.settings, "CHUNK_SIZE", 6),
            patch.object(routes.settings, "CHUNK_OVERLAP", 3),
            patch.object(chunker, "sent_tokenize", return_value=self.sentences),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def post(self, params=None):
        return self.client.post("/preprocess/", params=params, json=self.payload)

    def test_explicit_zero_overlap_disables_overlap(self):
        response = self.post({"chunk_overlap": 0})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_chunks"], 2)
        self.assertEqual(
            [chunk["text"] for chunk in body["chunks"]],
            [" ".join(self.sentences[:2]), " ".join(self.sentences[2:])],
        )
        for index, chunk in enumerate(body["chunks"]):
            self.assertEqual(chunk["doc_id"], "doc-123")
            self.assertEqual(chunk["chunk_id"], f"doc-123_chunk_{index:04d}")
            self.assertEqual(chunk["chunk_index"], index)
            self.assertEqual(chunk["total_chunks"], 2)
            self.assertEqual(chunk["word_count"], 6)
            self.assertEqual(chunk["char_count"], len(chunk["text"]))
            self.assertEqual(chunk["filename"], "example.txt")
            self.assertEqual(chunk["extra_metadata"], {"author": "Example"})

    def test_omitted_options_use_configured_defaults(self):
        response = self.post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [chunk["text"] for chunk in response.json()["chunks"]],
            [" ".join(self.sentences[i : i + 2]) for i in range(3)],
        )

    def test_explicit_positive_size_overrides_default(self):
        response = self.post({"chunk_size": 12, "chunk_overlap": 0})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_chunks"], 1)
        self.assertEqual(response.json()["chunks"][0]["text"], self.payload["text_content"])

    def test_explicit_positive_overlap_overrides_default(self):
        with patch.object(routes.settings, "CHUNK_OVERLAP", 0):
            response = self.post({"chunk_overlap": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_chunks"], 3)

    def test_zero_size_is_rejected(self):
        self.assert_query_rejected("chunk_size", 0)

    def test_negative_size_is_rejected(self):
        self.assert_query_rejected("chunk_size", -1)

    def test_negative_overlap_is_rejected(self):
        self.assert_query_rejected("chunk_overlap", -1)

    def test_non_integer_options_are_rejected(self):
        for field in ("chunk_size", "chunk_overlap"):
            with self.subTest(field=field):
                self.assert_query_rejected(field, "invalid")

    def assert_query_rejected(self, field, value):
        with patch.object(routes, "semantic_chunk") as semantic_chunk:
            response = self.post({field: value})

        self.assertEqual(response.status_code, 422)
        self.assertIn(
            ["query", field],
            [error["loc"] for error in response.json()["detail"]],
        )
        semantic_chunk.assert_not_called()


if __name__ == "__main__":
    unittest.main()
