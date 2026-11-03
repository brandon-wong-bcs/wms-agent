# Locations

## What it represents

Locations is the warehouse's address list. A location can be a picking slot, reserve storage position, staging area, or receiving dock. The sample locations are fictional.

## Columns and keys

| Column | Meaning |
|---|---|
| `location_id` | Text identifier for a warehouse location. Primary key; unique and required. |
| `zone` | Broad warehouse zone containing the location. Required. |
| `type` | Operational role, such as `PICKING`, `RESERVE`, `STAGING`, or `RECEIVING`. Required. |

Locations has no foreign keys. Inventory references `Locations.location_id`; a location can therefore be associated with multiple inventory rows.

## Example rows

| location_id | zone | type |
|---|---|---|
| P-01-01 | A | PICKING |
| R-02-01 | B | RESERVE |
| S-DOCK-01 | C | STAGING |

## Example queries

```sql
SELECT * FROM Locations WHERE type = 'PICKING';

SELECT location_id, zone, type
FROM Locations
WHERE zone = 'B'
ORDER BY location_id;

SELECT Locations.location_id, Locations.type, Inventory.sku, Inventory.quantity
FROM Locations
JOIN Inventory ON Inventory.location_id = Locations.location_id
WHERE Locations.location_id = 'R-02-01';
```

## Questions an eventual warehouse agent could answer

- Which locations are used for picking or reserve storage?
- What type of location is `R-02-01` and which zone is it in?
- What inventory is recorded at a given location, when combined with Inventory?
- Which locations currently have no inventory rows?