from __future__ import annotations

import json
import logging
import os
import platform
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOG = logging.getLogger(__name__)


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _coalesce_non_empty(*values: str | None) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def load_semantic_model_settings_from_env() -> dict[str, str]:
    """
    Load semantic model settings from environment variables.

    Supported vars (preferred):
    - STABLE_JARVIS_SEMANTIC_API_BASE_URL
    - STABLE_JARVIS_SEMANTIC_API_KEY
    - STABLE_JARVIS_SEMANTIC_MODEL

    Compatibility fallbacks:
    - OPENAI_BASE_URL
    - OPENAI_API_KEY
    - OPENAI_EMBEDDING_MODEL
    """
    return {
        "api_base_url": _coalesce_non_empty(
            os.getenv("STABLE_JARVIS_SEMANTIC_API_BASE_URL"),
            os.getenv("OPENAI_BASE_URL"),
        )
        or "",
        "api_key": _coalesce_non_empty(
            os.getenv("STABLE_JARVIS_SEMANTIC_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
        )
        or "",
        "model": _coalesce_non_empty(
            os.getenv("STABLE_JARVIS_SEMANTIC_MODEL"),
            os.getenv("OPENAI_EMBEDDING_MODEL"),
        )
        or "",
    }


def load_semantic_model_settings(api_keys_path: str | None = None) -> dict[str, str]:
    """
    Load semantic model settings from config/api_keys.json.

    Expected schema:
    {
      "semantic_model": {
        "api_base_url": "...",
        "api_key": "...",
        "model": "..."
      }
    }
    """
    candidate_paths: list[Path] = []
    if api_keys_path:
        candidate_paths.append(Path(api_keys_path).expanduser())
    env_path = os.getenv("STABLE_JARVIS_API_KEYS_PATH")
    if env_path:
        candidate_paths.append(Path(env_path).expanduser())
    candidate_paths.append(_workspace_root() / "config" / "api_keys.json")

    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        semantic_model = payload.get("semantic_model")
        if not isinstance(semantic_model, dict):
            continue
        return {
            "api_base_url": str(semantic_model.get("api_base_url") or "").strip(),
            "api_key": str(semantic_model.get("api_key") or "").strip(),
            "model": str(semantic_model.get("model") or "").strip(),
        }
    return {
        "api_base_url": "",
        "api_key": "",
        "model": "",
    }


@dataclass(slots=True)
class IndexedZoteroItem:
    item_id: int
    key: str
    item_type_id: int
    item_type: str | None = None
    doi: str | None = None
    title: str | None = None
    abstract: str | None = None
    creators: str | None = None
    fulltext: str | None = None
    fulltext_source: str | None = None
    notes: str | None = None
    extra: str | None = None
    date_added: str | None = None
    date_modified: str | None = None
    tags: list[str] | None = None
    collections: list[str] | None = None

    def searchable_text(self) -> str:
        parts: list[str] = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.creators:
            parts.append(f"Authors: {self.creators}")
        if self.abstract:
            parts.append(f"Abstract: {self.abstract}")
        if self.extra:
            parts.append(f"Extra: {self.extra}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        if self.tags:
            parts.append(f"Tags: {' '.join(self.tags)}")
        if self.collections:
            parts.append(f"Collections: {' '.join(self.collections)}")
        if self.fulltext:
            truncated = self.fulltext[:5000] + "..." if len(self.fulltext) > 5000 else self.fulltext
            parts.append(f"Content: {truncated}")
        return "\n\n".join(parts)


class LocalZoteroReader:
    def __init__(self, db_path: str | None = None, pdf_max_pages: int | None = None):
        self.db_path = db_path or self._find_zotero_db()
        self._connection: sqlite3.Connection | None = None
        self.pdf_max_pages = pdf_max_pages

    def _find_zotero_db(self) -> str:
        system = platform.system()
        if system == "Darwin":
            db_path = Path.home() / "Zotero" / "zotero.sqlite"
        elif system == "Windows":
            db_path = Path.home() / "Zotero" / "zotero.sqlite"
        else:
            db_path = Path.home() / "Zotero" / "zotero.sqlite"
        if not db_path.exists():
            raise FileNotFoundError(
                f"Zotero database not found at {db_path}. Please ensure Zotero is installed and has been run at least once."
            )
        return str(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            uri = f"file:{self.db_path}?immutable=1"
            self._connection = sqlite3.connect(uri, uri=True)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _resolve_collection_ids(self, names: list[str], *, library_id: int | None = None) -> list[int]:
        conn = self._get_connection()
        lowered = {name.strip().lower() for name in names if name.strip()}
        if not lowered:
            return []
        lib_clause = "AND c.libraryID = ?" if library_id is not None else ""
        lib_params: list[Any] = [library_id] if library_id is not None else []
        seeds: list[int] = []
        for row in conn.execute(f"SELECT c.collectionID, c.collectionName FROM collections c WHERE 1=1 {lib_clause}", lib_params):
            if row["collectionName"].strip().lower() in lowered:
                seeds.append(row["collectionID"])
        if not seeds:
            return []
        resolved = set(seeds)
        queue = list(seeds)
        while queue:
            current = queue.pop(0)
            for row in conn.execute("SELECT collectionID FROM collections WHERE parentCollectionID = ?", (current,)):
                child = row["collectionID"]
                if child not in resolved:
                    resolved.add(child)
                    queue.append(child)
        return sorted(resolved)

    def get_items_with_text(
        self,
        limit: int | None = None,
        include_fulltext: bool = False,
        *,
        library_id: int | None = None,
        collection_names: list[str] | None = None,
    ) -> list[IndexedZoteroItem]:
        del include_fulltext
        conn = self._get_connection()
        query = """
        SELECT
            i.itemID,
            i.key,
            i.itemTypeID,
            it.typeName as item_type,
            i.dateAdded,
            i.dateModified,
            title_val.value as title,
            abstract_val.value as abstract,
            extra_val.value as extra,
            doi_val.value as doi,
            (
                SELECT GROUP_CONCAT(n.note, ' ')
                FROM itemNotes n
                WHERE i.itemID = n.parentItemID OR i.itemID = n.itemID
            ) as notes,
            (
                SELECT GROUP_CONCAT(
                    CASE
                        WHEN c.firstName IS NOT NULL AND c.lastName IS NOT NULL
                        THEN c.lastName || ', ' || c.firstName
                        WHEN c.lastName IS NOT NULL
                        THEN c.lastName
                        ELSE NULL
                    END, '; '
                )
                FROM itemCreators ic
                JOIN creators c ON ic.creatorID = c.creatorID
                WHERE ic.itemID = i.itemID
            ) as creators,
            (
                SELECT GROUP_CONCAT(t.name, '||')
                FROM itemTags itg
                JOIN tags t ON t.tagID = itg.tagID
                WHERE itg.itemID = i.itemID
            ) as tags,
            (
                SELECT GROUP_CONCAT(c.collectionName, '||')
                FROM collectionItems ci
                JOIN collections c ON c.collectionID = ci.collectionID
                WHERE ci.itemID = i.itemID
            ) as collections
        FROM items i
        JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
        LEFT JOIN itemData title_data ON i.itemID = title_data.itemID AND title_data.fieldID = 1
        LEFT JOIN itemDataValues title_val ON title_data.valueID = title_val.valueID
        LEFT JOIN itemData abstract_data ON i.itemID = abstract_data.itemID AND abstract_data.fieldID = 2
        LEFT JOIN itemDataValues abstract_val ON abstract_data.valueID = abstract_val.valueID
        LEFT JOIN itemData extra_data ON i.itemID = extra_data.itemID AND extra_data.fieldID = 16
        LEFT JOIN itemDataValues extra_val ON extra_data.valueID = extra_val.valueID
        LEFT JOIN fields doi_f ON doi_f.fieldName = 'DOI'
        LEFT JOIN itemData doi_data ON i.itemID = doi_data.itemID AND doi_data.fieldID = doi_f.fieldID
        LEFT JOIN itemDataValues doi_val ON doi_data.valueID = doi_val.valueID
        WHERE it.typeName NOT IN ('attachment', 'note', 'annotation')
        ORDER BY i.dateModified DESC
        """
        params: list[Any] = []
        if library_id is not None:
            query = query.replace(
                "WHERE it.typeName NOT IN ('attachment', 'note', 'annotation')",
                "WHERE it.typeName NOT IN ('attachment', 'note', 'annotation') AND i.libraryID = ?",
            )
            params.append(int(library_id))
        if collection_names:
            coll_ids = self._resolve_collection_ids(collection_names, library_id=library_id)
            if coll_ids:
                placeholders = ",".join("?" for _ in coll_ids)
                query = query.replace(
                    "ORDER BY i.dateModified DESC",
                    f"AND i.itemID IN (SELECT ci.itemID FROM collectionItems ci WHERE ci.collectionID IN ({placeholders})) ORDER BY i.dateModified DESC",
                )
                params.extend(coll_ids)
            else:
                return []
        if limit:
            query += f" LIMIT {int(limit)}"

        items: list[IndexedZoteroItem] = []
        for row in conn.execute(query, params):
            items.append(
                IndexedZoteroItem(
                    item_id=row["itemID"],
                    key=row["key"],
                    item_type_id=row["itemTypeID"],
                    item_type=row["item_type"],
                    doi=row["doi"],
                    title=row["title"],
                    abstract=row["abstract"],
                    creators=row["creators"],
                    notes=row["notes"],
                    extra=row["extra"],
                    date_added=row["dateAdded"],
                    date_modified=row["dateModified"],
                    tags=[tag for tag in str(row["tags"] or "").split("||") if tag],
                    collections=[name for name in str(row["collections"] or "").split("||") if name],
                )
            )
        return items


class OpenAIEmbeddingFunction:
    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str | None = None, base_url: str | None = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        try:
            import openai
        except ImportError as exc:
            raise ImportError("openai package is required for semantic ranking") from exc
        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self.client = openai.OpenAI(**client_kwargs)

    def __call__(self, input_texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model_name, input=input_texts)
        return [item.embedding for item in response.data]


@dataclass(slots=True)
class SemanticConfig:
    db_path: str | None = None
    chroma_dir: str = ".state/chroma/paper_finder"
    collection_name: str = "stable_jarvis_paper_finder"
    library_id: int | None = None
    collection_names: list[str] | None = None
    embedding_model: str = "text-embedding-3-small"
    api_key: str | None = None
    base_url: str | None = None
    api_keys_path: str | None = None
    include_fulltext: bool = False
    reindex: bool = False


def build_semantic_search_fn(config: SemanticConfig):
    try:
        import chromadb
    except ImportError as exc:
        raise ImportError("chromadb is required for semantic ranking") from exc

    semantic_env_settings = load_semantic_model_settings_from_env()
    semantic_model_settings = load_semantic_model_settings(config.api_keys_path)
    resolved_base_url = _coalesce_non_empty(
        config.base_url,
        semantic_env_settings.get("api_base_url"),
        semantic_model_settings.get("api_base_url"),
    )
    resolved_api_key = _coalesce_non_empty(
        config.api_key,
        semantic_env_settings.get("api_key"),
        semantic_model_settings.get("api_key"),
    )
    default_model = SemanticConfig.__dataclass_fields__["embedding_model"].default
    resolved_model = config.embedding_model
    if resolved_model == default_model:
        resolved_model = _coalesce_non_empty(
            semantic_env_settings.get("model"),
            semantic_model_settings.get("model"),
            resolved_model,
        ) or default_model

    chroma_dir = Path(config.chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    embedding_function = OpenAIEmbeddingFunction(
        model_name=resolved_model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
    )
    client = chromadb.PersistentClient(path=str(chroma_dir))
    if config.reindex:
        try:
            client.delete_collection(config.collection_name)
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=config.collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )
    if collection.count() == 0 or config.reindex:
        reader = LocalZoteroReader(config.db_path)
        items = reader.get_items_with_text(
            include_fulltext=config.include_fulltext,
            library_id=config.library_id,
            collection_names=config.collection_names,
        )
        if not items:
            raise ValueError("No Zotero items were found for semantic indexing")
        collection.upsert(
            ids=[item.key for item in items],
            documents=[item.searchable_text() for item in items],
            metadatas=[
                {
                    "title": item.title or "",
                    "collections": "||".join(item.collections or []),
                    "doi": item.doi or "",
                }
                for item in items
            ],
        )

    def semantic_search(query_text: str, top_k: int = 3) -> dict[str, Any]:
        response = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["metadatas", "distances"],
        )
        ids = response.get("ids", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]
        results: list[dict[str, Any]] = []
        for item_key, metadata, distance in zip(ids, metadatas, distances, strict=False):
            metadata = metadata or {}
            results.append(
                {
                    "item_key": item_key,
                    "distance": distance,
                    "metadata": {
                        "title": metadata.get("title") or None,
                        "collections": [
                            value for value in str(metadata.get("collections") or "").split("||") if value
                        ],
                    },
                }
            )
        return {"results": results}

    return semantic_search
