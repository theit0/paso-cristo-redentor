"""Almacenamiento append-only en JSONL: data/<tipo>/<AAAA-MM>.jsonl.

Texto y solo-agregar: se versiona bien en la rama `data` que llena GitHub Actions.
"""
import json
from collections.abc import Iterator

from app import config


def append(kind: str, record: dict) -> None:
    path = config.DATA_DIR / kind / f"{record['fetched_at'][:7]}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ponytail: lee archivos mensuales enteros; pasar a SQLite/Parquet si las lecturas se vuelven lentas.
def newest_first(kind: str) -> Iterator[dict]:
    for path in sorted((config.DATA_DIR / kind).glob("*.jsonl"), reverse=True):
        for line in reversed(path.read_text(encoding="utf-8").splitlines()):
            yield json.loads(line)
