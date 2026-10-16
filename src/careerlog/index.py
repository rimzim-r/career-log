import chromadb

from .schema import LogEntry

DB_PATH = "chroma_db"
COLLECTION = "career_log"


def get_collection(db_path: str = DB_PATH):
    client = chromadb.PersistentClient(path=str(db_path))
    return client.get_or_create_collection(COLLECTION)


def build_index(entries: list[LogEntry], db_path: str = DB_PATH) -> int:
    """Embed every entry and store it. Safe to re-run: same id = overwrite."""
    if not entries:
        return 0
    col = get_collection(db_path)
    col.upsert(
        ids=[e.id for e in entries],
        documents=[e.text for e in entries],
        metadatas=[
            {
                "date": e.date.isoformat(),
                "tags": ",".join(e.tags),
                "source": e.source,
                "link": e.link or "",
            }
            for e in entries
        ],
    )
    return len(entries)


def search(query: str, k: int = 5, db_path: str = DB_PATH) -> list[dict]:
    """Return the k entries closest in meaning to the query."""
    col = get_collection(db_path)
    res = col.query(query_texts=[query], n_results=k)
    hits = []
    for i in range(len(res["ids"][0])):
        hits.append({
            "id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "distance": res["distances"][0][i],
            **res["metadatas"][0][i],
        })
    return hits