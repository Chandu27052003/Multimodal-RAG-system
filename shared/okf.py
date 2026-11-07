"""Read a bounded, data-only subset of Open Knowledge Format v0.2.

This is an offline preparation adapter, not a full conformance validator or
an execution engine. It never follows links, evaluates code, or verifies facts.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

import yaml


MAX_FILE_BYTES = 1024 * 1024
MAX_BUNDLE_BYTES = 8 * MAX_FILE_BYTES
MAX_ENTRIES = 1000
MAX_DIRECTORY_DEPTH = 32
RESERVED_NAMES = {"index.md", "log.md"}


class OKFError(ValueError):
    """An input cannot be safely prepared by this adapter."""


class _DataLoader(yaml.SafeLoader):
    """Bound YAML complexity and disallow ambiguous keys/alias expansion."""

    def __init__(self, stream):
        super().__init__(stream)
        self._depth = 0
        self._nodes = 0

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise OKFError("YAML aliases are not supported by the safety profile")
        self._nodes += 1
        self._depth += 1
        try:
            if self._depth > 32 or self._nodes > 10000:
                raise OKFError("YAML complexity limit exceeded")
            return super().compose_node(parent, index)
        finally:
            self._depth -= 1

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise OKFError("Frontmatter mapping keys must be strings")
            if key in mapping:
                raise OKFError(f"Duplicate frontmatter key: {key}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


# Keep timestamps as their written strings so JSON export preserves the offset.
_DataLoader.add_constructor(
    "tag:yaml.org,2002:timestamp", _DataLoader.construct_scalar
)


@dataclass(frozen=True)
class Concept:
    path: str
    frontmatter: dict
    body: str

    @property
    def concept_id(self) -> str:
        return self.path[:-3]

    def preprocessing_request(self, bundle_id: str) -> dict:
        """Produce the existing preprocessing API's request shape, without I/O."""
        if not isinstance(bundle_id, str) or not bundle_id.strip():
            raise OKFError("A non-empty bundle_id namespace is required")
        identity = json.dumps([bundle_id, self.concept_id], ensure_ascii=False)
        doc_id = "okf_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return {
            "doc_id": doc_id,
            "source_type": "okf",
            "filename": self.path,
            "text_content": self.body,
            "extra_metadata": {
                "okf": {
                    "bundle_id": bundle_id,
                    "concept_id": self.concept_id,
                    "frontmatter": self.frontmatter,
                }
            },
        }


def parse_concept(text: str, path: str) -> Concept:
    """Parse one concept, preserving unknown types, fields, links and body."""
    parts = path.split("/")
    if (
        not path
        or any(p in {"", ".", ".."} for p in parts)
        or "\\" in path
        or "\x00" in path
        or not path.endswith(".md")
        or PurePosixPath(path).name in RESERVED_NAMES
    ):
        raise OKFError("Concept path must be a non-reserved relative .md path")
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise OKFError("Concept exceeds the 1 MiB size limit")
    lines = text.removeprefix("\ufeff").splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise OKFError("Concept must start with YAML frontmatter")
    closing = next(
        (i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"),
        None,
    )
    if closing is None:
        raise OKFError("Missing closing frontmatter delimiter")
    try:
        metadata = yaml.load("".join(lines[1:closing]), Loader=_DataLoader)
        # JSON is the downstream preprocessing API's transport format.
        serialized = json.dumps(metadata, allow_nan=False)
        if json.loads(serialized) != metadata:
            raise OKFError("Frontmatter must use JSON-compatible values")
    except (yaml.YAMLError, TypeError, ValueError, OverflowError) as exc:
        raise OKFError(f"Invalid data-only frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise OKFError("Frontmatter must be a mapping")
    if not isinstance(metadata.get("type"), str) or not metadata["type"].strip():
        raise OKFError("Frontmatter requires a non-empty string type")
    # Spec §5.2 requires consumers to treat a bare verified event as a list.
    if isinstance(metadata.get("verified"), dict):
        metadata["verified"] = [metadata["verified"]]
    return Concept(path, metadata, "".join(lines[closing + 1 :]))


def load_bundle(root: Path) -> list[Concept]:
    """Load a directory deterministically; never traverse symbolic links.

    Reserved index/log files are excluded, not validated. Git's metadata
    directory is ignored. All other .md files must parse before output is made.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise OKFError("Bundle root must be a real directory, not a symlink")
    concepts = []
    total_bytes = 0
    entries = 0

    def fail_walk(error):
        raise OKFError(f"Cannot read bundle directory: {error}") from error

    for current, directories, files in os.walk(root, followlinks=False, onerror=fail_walk):
        if len(Path(current).relative_to(root).parts) > MAX_DIRECTORY_DEPTH:
            raise OKFError("Bundle directory depth limit exceeded")
        directories[:] = sorted(d for d in directories if d != ".git")
        entries += len(directories) + len(files)
        if entries > MAX_ENTRIES:
            raise OKFError("Bundle exceeds the 1000-entry limit")
        for name in directories + files:
            if (Path(current) / name).is_symlink():
                raise OKFError("Symlinks are not supported inside bundles")
        for name in sorted(files):
            if not name.endswith(".md") or name in RESERVED_NAMES:
                continue
            path = Path(current) / name
            if not path.is_file():
                raise OKFError("Concept must be a regular file")
            with path.open("rb") as handle:
                raw = handle.read(MAX_FILE_BYTES + 1)
            total_bytes += len(raw)
            if len(raw) > MAX_FILE_BYTES or total_bytes > MAX_BUNDLE_BYTES:
                raise OKFError("Bundle or concept size limit exceeded")
            relative = path.relative_to(root).as_posix()
            try:
                concepts.append(parse_concept(raw.decode("utf-8"), relative))
            except (UnicodeError, OKFError) as exc:
                raise OKFError(f"{relative}: {exc}") from exc
    if not concepts:
        raise OKFError("Bundle contains no concept documents")
    return sorted(concepts, key=lambda concept: concept.path)
