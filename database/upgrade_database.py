import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "warehouse.db"
SCHEMA = BASE_DIR / "database" / "schema.sql"
SEED = BASE_DIR / "database" / "seed.sql"


connection = sqlite3.connect(DATABASE)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA, "r") as file:
        connection.executescript(file.read())

    with open(SEED, "r") as file:
        connection.executescript(file.read())

    connection.commit()

    print("Database upgraded successfully.")

finally:
    connection.close()