"""Create warehouse.db from the readable SQL schema and seed scripts."""

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "warehouse.db"
SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")
SEED_PATH = Path(__file__).resolve().with_name("seed.sql")


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        # SQLite foreign keys must be enabled separately for each connection.
        connection.execute("PRAGMA foreign_keys = ON;")

        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        seed_sql = SEED_PATH.read_text(encoding="utf-8")
        connection.executescript(schema_sql)
        print(f"Created or verified tables in {DATABASE_PATH.name}.")

        connection.executescript(seed_sql)
        print("Loaded synthetic products, locations, and inventory.")

        foreign_key_errors = connection.execute("PRAGMA foreign_key_check;").fetchall()
        if foreign_key_errors:
            raise sqlite3.IntegrityError(
                f"Foreign key check found problems: {foreign_key_errors}"
            )

        print("Foreign key check passed.")
        print(f"Database is ready: {DATABASE_PATH}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()