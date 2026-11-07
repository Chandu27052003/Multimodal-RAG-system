import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from shared.okf import MAX_FILE_BYTES, OKFError, load_bundle, parse_concept
from tools.prepare_okf import main


MINIMAL = "---\ntype: Reference\n---\nA useful fact.\n"


class ParseTests(unittest.TestCase):
    def test_minimal_concept(self):
        result = parse_concept(MINIMAL, "notes/item.md")
        self.assertEqual(result.concept_id, "notes/item")
        self.assertEqual(result.frontmatter, {"type": "Reference"})
        self.assertEqual(result.body, "A useful fact.\n")

    def test_bom_crlf_and_body_are_preserved(self):
        body = "\r\n# తెలుగు\r\n\r\n```sql\r\nSELECT 1;\r\n```\r\n"
        result = parse_concept("\ufeff---\r\ntype: Query\r\n---\r\n" + body, "q.md")
        self.assertEqual(result.body, body)

    def test_empty_body_is_allowed(self):
        self.assertEqual(parse_concept("---\ntype: Future\n---", "f.md").body, "")

    def test_unknown_type_and_nested_extensions_are_preserved(self):
        text = "---\ntype: CustomType\ncustom:\n  nested: [1, true, null, hello]\n---\n"
        self.assertEqual(parse_concept(text, "a.md").frontmatter["custom"],
                         {"nested": [1, True, None, "hello"]})

    def test_provenance_dates_and_lifecycle_are_preserved(self):
        text = """---
type: Audio Transcript
sources:
  - id: source-1
    resource: https://example.invalid/video#t=32
    last_modified: 2026-06-01T12:00:00+05:30
generated: {by: process:transcriber, at: 2026-06-02T00:00:00Z}
stale_after: 2026-12-01T00:00:00Z
status: deprecated
tags: [audio, example]
---
An attributed claim.[^source-1]

[^source-1]: A transcript.
"""
        meta = parse_concept(text, "a.md").frontmatter
        self.assertEqual(meta["sources"][0]["last_modified"], "2026-06-01T12:00:00+05:30")
        self.assertEqual(meta["stale_after"], "2026-12-01T00:00:00Z")
        self.assertEqual(meta["status"], "deprecated")
        json.dumps(meta, allow_nan=False)

    def test_single_verification_mapping_becomes_list(self):
        text = "---\ntype: Reference\nverified: {by: human:sample, at: 2026-06-01T00:00:00Z}\n---\n"
        self.assertEqual(parse_concept(text, "a.md").frontmatter["verified"],
                         [{"by": "human:sample", "at": "2026-06-01T00:00:00Z"}])

    def test_verification_list_is_preserved(self):
        text = "---\ntype: Reference\nverified:\n  - by: process:test\n---\n"
        self.assertEqual(parse_concept(text, "a.md").frontmatter["verified"], [{"by": "process:test"}])

    def test_no_trust_or_freshness_is_fabricated(self):
        self.assertEqual(set(parse_concept(MINIMAL, "a.md").frontmatter), {"type"})

    def test_broken_links_and_code_remain_inert_text(self):
        body = '[Missing](/not-written.md) ![image](https://example.invalid/a.png)\n```python\nraise Exception()\n```'
        result = parse_concept("---\ntype: Attested Computation\n---\n" + body, "a.md")
        self.assertEqual(result.body, body)

    def test_invalid_headers(self):
        for text in ["body", "\n---\ntype: X\n---", "---\ntype: X", "---\n[]\n---",
                     "---\n{}\n---", "---\ntype: null\n---", "---\ntype: ''\n---",
                     "---\ntype: 7\n---", "---\ntype: [X]\n---", "---\ntype: [\n---"]:
            with self.subTest(text=text), self.assertRaises(OKFError):
                parse_concept(text, "a.md")

    def test_invalid_paths(self):
        for path in ["", "/a.md", "../a.md", "a/../b.md", "a//b.md", "./a.md",
                     "a\\b.md", "a.txt", "index.md", "nested/log.md", "a\0.md"]:
            with self.subTest(path=path), self.assertRaises(OKFError):
                parse_concept(MINIMAL, path)

    def test_duplicate_keys_rejected_including_nested(self):
        for fields in ["type: X\ntype: Y", "type: X\nx: {a: 1, a: 2}"]:
            with self.subTest(fields=fields), self.assertRaisesRegex(OKFError, "Duplicate"):
                parse_concept(f"---\n{fields}\n---\n", "a.md")

    def test_nonstring_mapping_keys_rejected(self):
        with self.assertRaisesRegex(OKFError, "keys must be strings"):
            parse_concept("---\ntype: X\nx: {1: value}\n---\n", "a.md")

    def test_yaml_object_construction_is_rejected(self):
        text = "---\ntype: X\nx: !!python/object/apply:os.system ['echo forbidden']\n---\n"
        with patch("os.system") as execute, self.assertRaises(OKFError):
            parse_concept(text, "a.md")
        execute.assert_not_called()

    def test_aliases_and_cycles_rejected(self):
        for fields in ["type: X\nx: &x [*x]", "type: X\nx: &x hello\ny: *x"]:
            with self.subTest(fields=fields), self.assertRaisesRegex(OKFError, "aliases"):
                parse_concept(f"---\n{fields}\n---\n", "a.md")

    def test_deep_yaml_rejected(self):
        text = "---\ntype: X\nx: " + "[" * 40 + "0" + "]" * 40 + "\n---\n"
        with self.assertRaisesRegex(OKFError, "complexity"):
            parse_concept(text, "a.md")

    def test_many_yaml_nodes_rejected(self):
        text = "---\ntype: X\nx: [" + ",".join(["0"] * 10001) + "]\n---\n"
        with self.assertRaisesRegex(OKFError, "complexity"):
            parse_concept(text, "a.md")

    def test_non_json_values_rejected(self):
        for value in [".nan", ".inf", "!!binary aGVsbG8=", "!!set {a: null}",
                      "!!omap [{a: b}]", "!!pairs [{a: b}]"]:
            with self.subTest(value=value), self.assertRaises(OKFError):
                parse_concept(f"---\ntype: X\nx: {value}\n---\n", "a.md")

    def test_file_limit_is_bytes_not_characters(self):
        with self.assertRaisesRegex(OKFError, "size limit"):
            parse_concept(MINIMAL + "é" * (MAX_FILE_BYTES // 2), "a.md")

    def test_global_yaml_loader_is_unchanged(self):
        import datetime
        self.assertIsInstance(yaml.safe_load("2026-01-01"), datetime.date)


class AdapterTests(unittest.TestCase):
    def test_stable_namespaced_ids(self):
        a = parse_concept(MINIMAL, "a.md")
        self.assertEqual(a.preprocessing_request("one"), a.preprocessing_request("one"))
        self.assertNotEqual(a.preprocessing_request("one")["doc_id"], a.preprocessing_request("two")["doc_id"])
        self.assertNotEqual(a.preprocessing_request("one")["doc_id"],
                            parse_concept(MINIMAL, "b.md").preprocessing_request("one")["doc_id"])

    def test_content_change_preserves_identity(self):
        before = parse_concept(MINIMAL, "a.md").preprocessing_request("one")
        after = parse_concept(MINIMAL + "More.", "a.md").preprocessing_request("one")
        self.assertEqual(before["doc_id"], after["doc_id"])
        self.assertNotEqual(before["text_content"], after["text_content"])

    def test_blank_namespace_rejected(self):
        for namespace in ["", "  ", None]:
            with self.subTest(namespace=namespace), self.assertRaises(OKFError):
                parse_concept(MINIMAL, "a.md").preprocessing_request(namespace)

    def test_real_preprocessing_schema_and_chunk_metadata(self):
        from services.preprocessing.app.metadata import build_chunk_results
        from services.preprocessing.app.models import PreprocessRequest

        request = parse_concept(MINIMAL, "a.md").preprocessing_request("demo")
        validated = PreprocessRequest(**request)
        chunks = build_chunk_results(validated.doc_id, validated.source_type, validated.filename,
                                     validated.extra_metadata, ["first chunk", "second chunk"])
        self.assertEqual(len(chunks), 2)
        for chunk in chunks:
            self.assertEqual(chunk.extra_metadata, request["extra_metadata"])
            self.assertEqual(chunk.source_type, "okf")


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, text=MINIMAL):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        return destination

    def test_recursive_sorted_discovery_excludes_reserved_and_git(self):
        self.write("z.md")
        self.write("a/b.md")
        self.write("a/index.md", "# Index")
        self.write("log.md", "# History")
        self.write(".git/ignored.md", "not a concept")
        self.write("image.png", "not a real image")
        self.assertEqual([c.path for c in load_bundle(self.root)], ["a/b.md", "z.md"])

    def test_unknown_declared_version_does_not_reject_concepts(self):
        self.write("index.md", '---\nokf_version: "99.0"\n---\n# Index')
        self.write("a.md")
        self.assertEqual(len(load_bundle(self.root)), 1)

    def test_empty_or_missing_bundle_rejected(self):
        for root in [self.root, self.root / "missing"]:
            with self.subTest(root=root), self.assertRaises(OKFError):
                load_bundle(root)

    def test_invalid_utf8_is_reported(self):
        (self.root / "a.md").write_bytes(b"\xff")
        with self.assertRaisesRegex(OKFError, "a.md"):
            load_bundle(self.root)

    def test_symlink_file_rejected(self):
        target = self.write("a.md")
        (self.root / "link.md").symlink_to(target)
        with self.assertRaisesRegex(OKFError, "Symlinks"):
            load_bundle(self.root)

    def test_symlink_directory_and_root_rejected(self):
        (self.root / "loop").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(OKFError, "Symlinks"):
            load_bundle(self.root)
        with self.assertRaisesRegex(OKFError, "symlink"):
            load_bundle(self.root / "loop")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX named pipes only")
    def test_named_pipe_rejected_without_reading(self):
        os.mkfifo(self.root / "pipe.md")
        with self.assertRaisesRegex(OKFError, "regular file"):
            load_bundle(self.root)

    def test_per_file_size_bound(self):
        self.write("large.md", MINIMAL + "x" * MAX_FILE_BYTES)
        with self.assertRaisesRegex(OKFError, "size limit"):
            load_bundle(self.root)

    def test_bundle_size_bound(self):
        self.write("a.md")
        self.write("b.md")
        with patch("shared.okf.MAX_BUNDLE_BYTES", len(MINIMAL.encode()) + 1):
            with self.assertRaisesRegex(OKFError, "size limit"):
                load_bundle(self.root)

    def test_entry_count_bound(self):
        self.write("a.md")
        self.write("b.md")
        with patch("shared.okf.MAX_ENTRIES", 1):
            with self.assertRaisesRegex(OKFError, "entry"):
                load_bundle(self.root)

    def test_directory_depth_bound(self):
        self.write("/".join(["nested"] * 34) + "/a.md")
        with self.assertRaisesRegex(OKFError, "directory depth"):
            load_bundle(self.root)

    def test_cli_has_no_partial_output_on_invalid_bundle(self):
        self.write("a.md")
        self.write("z.md", "invalid")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main([str(self.root), "--bundle-id", "test"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("z.md", err.getvalue())

    def test_cli_process_outputs_jsonl(self):
        self.write("a.md")
        self.write("b.md")
        result = subprocess.run([sys.executable, "-m", "tools.prepare_okf", str(self.root),
                                 "--bundle-id", "demo"], capture_output=True, text=True,
                                cwd=Path(__file__).resolve().parents[1], timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        records = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["text_content"], "A useful fact.\n")
        self.assertEqual(records[1]["extra_metadata"]["okf"]["concept_id"], "b")


if __name__ == "__main__":
    unittest.main()
