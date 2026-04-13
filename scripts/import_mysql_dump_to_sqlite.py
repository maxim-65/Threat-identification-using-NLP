import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SQL_DUMP_PATH = BASE_DIR.parent.parent / "Database" / "automated_emerging_cyber_threat_identification.sql"
SQLITE_DB_PATH = BASE_DIR.parent / "db.sqlite3"


def _normalize_sql(mysql_sql: str) -> str:
    lines = []
    in_create_table = False
    for raw_line in mysql_sql.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("--"):
            continue
        if line.startswith("/*") or line.startswith("*/") or line.startswith("/*!"):
            continue
        if line.startswith("SET "):
            continue
        if line.startswith("CREATE DATABASE"):
            continue
        if line.startswith("USE "):
            continue

        # Track CREATE TABLE blocks so we can normalize id definitions.
        if line.upper().startswith("CREATE TABLE"):
            in_create_table = True

        # SQLite does not support MySQL AUTO_INCREMENT table metadata.
        line = re.sub(r"\bAUTO_INCREMENT=\d+\b", "", line)
        # Keep implicit rowid behavior via INTEGER PRIMARY KEY.
        line = line.replace("AUTO_INCREMENT", "")
        line = re.sub(r"\bunsigned\b", "", line, flags=re.IGNORECASE)

        # Convert MySQL id definitions so inserts work without explicit ids.
        if in_create_table and re.match(r"^id\s+int\(\d+\)\s+NOT NULL\s*,?$", line, flags=re.IGNORECASE):
            line = "id INTEGER PRIMARY KEY AUTOINCREMENT,"

        # Drop duplicate PK line after converting id column above.
        if in_create_table and re.match(r"^PRIMARY KEY\s*\(\s*id\s*\)\s*,?$", line, flags=re.IGNORECASE):
            continue

        # Drop MySQL-specific table options.
        line = re.sub(r"\)\s*ENGINE=.*", ");", line)

        # Remove unsupported index definitions inside CREATE TABLE blocks.
        if line.startswith("KEY "):
            continue
        if line.startswith("UNIQUE KEY"):
            continue

        if in_create_table and line.endswith(");"):
            in_create_table = False

        lines.append(line)

    sql = "\n".join(lines)
    sql = sql.replace("`", "")
    sql = re.sub(r",\s*\)", ")", sql)
    return sql


def import_dump_to_sqlite() -> None:
    if not SQL_DUMP_PATH.exists():
        raise FileNotFoundError(f"SQL dump not found: {SQL_DUMP_PATH}")

    mysql_sql = SQL_DUMP_PATH.read_text(encoding="utf-8", errors="ignore")
    sqlite_sql = _normalize_sql(mysql_sql)

    if SQLITE_DB_PATH.exists():
        SQLITE_DB_PATH.unlink()

    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        conn.executescript("PRAGMA foreign_keys = OFF;")
        conn.executescript(sqlite_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"SQLite database created at: {SQLITE_DB_PATH}")


if __name__ == "__main__":
    import_dump_to_sqlite()
