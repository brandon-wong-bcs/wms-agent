# Warehouse Database

## Purpose

`warehouse.db` is a small SQLite database representing the inventory portion of a fictional warehouse. It stores a product catalog, warehouse locations, and the quantity/status of each product at each location. Every record is synthetic.

SQLite is used because it is included with Python through the built-in `sqlite3` module. It needs no database server or third-party package, so the SQL and resulting data are easy to inspect while learning.

## Structure and relationships

```text
Products (sku, name, unit)       Locations (location_id, zone, type)
          1 \                                  / 1
             \                                /
              * Inventory (inventory_id, sku, location_id, quantity, status)
```

Each Inventory row refers to exactly one Products row and one Locations row. One product can have inventory rows in multiple locations, and one location can contain multiple products. This is a one-to-many relationship from Products to Inventory and from Locations to Inventory.

The primary key uniquely identifies a row in its table. A foreign key is a column whose value must match a key in a related table; here they prevent inventory from referring to a product or location that does not exist. Foreign-key enforcement is enabled on the connection that creates and seeds the database.

## Create or recreate the database

From the project root in PowerShell, run:

```powershell
py -3.13 database\create_database.py
```

The script creates `warehouse.db` if it is missing, creates tables if needed, and loads seed rows. The seed uses `INSERT OR IGNORE`, so rerunning the command does not duplicate its rows. To start over with a completely fresh database, close any program using it and remove `warehouse.db` before running the command again.

The SQL definitions live in `database/schema.sql`; the sample rows live in `database/seed.sql`. Python's `sqlite3` code in `database/create_database.py` opens the database and executes those scripts.

## Inspect the data

With Python, run this from the project root:

```powershell
py -3.13 -c "import sqlite3; db=sqlite3.connect('warehouse.db'); print(db.execute('SELECT * FROM Inventory').fetchall()); db.close()"
```

Alternatively, open `warehouse.db` with a SQLite viewer. To inspect table definitions in SQL:

```sql
SELECT name, sql
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
```

## Tables

- **Products**: synthetic product catalog, keyed by SKU.
- **Locations**: warehouse areas, keyed by location ID.
- **Inventory**: quantities and statuses connecting products with locations.