from langchain_core.documents import Document
from langchain_core.stores import BaseStore
from typing import override, Sequence, Iterator, TypeVar, Generic

# import psycopg2, json
import json


class PostgresDocStore(BaseStore[str, Document]):

    def __init__(self, conn):
        self.conn = conn

    @override
    def mget(self, keys: Sequence[str]) -> list[Document | None]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, metadata FROM parent_documents WHERE id = ANY(%s)",
                (keys,),
            )
            rows = {
                r[0]: Document(page_content=r[1], metadata=r[2]) for r in cur.fetchall()
            }
        return [rows.get(k) for k in keys if k in rows]

    @override
    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        with self.conn.cursor() as cur:
            for key, doc in key_value_pairs:
                cur.execute(
                    """
                    INSERT INTO parent_documents (id, content, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET content = EXCLUDED.content, metadata = EXCLUDED.metadata
                    """,
                    (key, doc.page_content, json.dumps(doc.metadata)),
                )
        self.conn.commit()

    @override
    def mdelete(self, keys: Sequence[str]) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM parent_documents WHERE id = ANY(%s)",
                (keys,),
            )
        self.conn.commit()

    @override
    def yield_keys(self, *, prefix=None) -> Iterator[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM parent_documents")
            for (id_,) in cur.fetchall():
                yield id_
