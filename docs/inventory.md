# Inventory

## What it represents

Inventory records quantities of SKUs stored at warehouse locations, along with an operational status. A SKU may have separate rows for several locations and statuses. The sample balances and statuses are synthetic.

## Columns and keys

| Column | Meaning |
|---|---|
| `inventory_id` | Database-generated integer primary key for this balance row. |
| `sku` | Product identifier; required foreign key to `Products.sku`. |
| `location_id` | Warehouse location; required foreign key to `Locations.location_id`. |
| `quantity` | Number of units represented by this row. Required and constrained to be zero or greater. |
| `status` | Inventory state, such as `AVAILABLE` or `HOLD`. Required. |

The primary key distinguishes inventory rows. The two foreign keys ensure the referenced product and location exist. Products has a one-to-many relationship with Inventory, as does Locations. Each inventory row connects one product to one location.

## Example rows

| inventory_id | sku | location_id | quantity | status |
|---:|---|---|---:|---|
| 1 | A100 | P-01-01 | 18 | AVAILABLE |
| 2 | A100 | R-02-01 | 72 | AVAILABLE |
| 3 | A100 | S-DOCK-01 | 4 | HOLD |

## Example queries

```sql
SELECT * FROM Inventory WHERE sku = 'A100';

SELECT sku, SUM(quantity) AS total_quantity
FROM Inventory
WHERE status = 'AVAILABLE'
GROUP BY sku;

SELECT Inventory.sku, Products.name, Locations.location_id,
       Locations.zone, Locations.type, Inventory.quantity, Inventory.status
FROM Inventory
JOIN Products ON Products.sku = Inventory.sku
JOIN Locations ON Locations.location_id = Inventory.location_id
ORDER BY Inventory.sku, Locations.location_id;
```

## Questions an eventual warehouse agent could answer

- How much of a SKU is recorded at a particular location?
- Which locations contain a SKU, and what are the statuses there?
- What is the total available quantity for a SKU across the warehouse?
- Which quantities are on hold, and where are they recorded?