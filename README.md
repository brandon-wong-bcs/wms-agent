# Synthetic Warehouse Inventory

## Purpose

This learning project creates a small, completely synthetic SQLite database for the inventory portion of a warehouse management system (WMS). It is designed to make the schema, seed data, and database creation process easy to read. The database can later serve as the environment queried by an AI warehouse agent; this project does not build that agent.

## Project structure

```text
Agent/
├── .venv/                     # Optional Python virtual environment
├── database/
│   ├── create_database.py     # Opens the database and runs the SQL scripts
│   ├── schema.sql             # Table definitions and constraints
│   └── seed.sql               # Small synthetic dataset
├── docs/
│   ├── database.md
│   ├── products.md
│   ├── locations.md
│   └── inventory.md
├── warehouse.db               # Created by the script
└── README.md
```

## Set up Python on Windows PowerShell

Python 3.13 is expected. From the project root, create a virtual environment:

```powershell
py -3.13 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

No additional Python packages are needed. Python's built-in `sqlite3` module is used.

## Create the database

From the project root, run:

```powershell
py -3.13 database\create_database.py
```

This creates `warehouse.db` in the project root, creates the tables from `database/schema.sql`, and inserts the examples in `database/seed.sql`. It also enables and checks SQLite foreign keys. The seed statements can be run repeatedly without duplicating their rows. To recreate from a blank database, delete `warehouse.db` and run the command again.

## Inspect the database

Use a SQLite viewer to open `warehouse.db`, or run a quick query from PowerShell:

```powershell
py -3.13 -c "import sqlite3; db=sqlite3.connect('warehouse.db'); print(db.execute('SELECT * FROM Inventory').fetchall()); db.close()"
```

## Tables

- **Products** stores a unique SKU, product name, and counting unit.
- **Locations** stores a unique location ID, zone, and operational type.
- **Inventory** stores quantity and status for a SKU at a location. Its SKU and location ID are foreign keys to Products and Locations.

See [docs/database.md](docs/database.md) for the relationships and database workflow, and the individual table guides for columns, queries, and example agent questions.