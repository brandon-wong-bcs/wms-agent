# Products

## What it represents

Products is the warehouse catalog: one row per kind of item that may be stored or moved. The sample catalog is entirely synthetic.

## Columns and keys

| Column | Meaning |
|---|---|
| `sku` | Text stock-keeping unit used to identify a product. Primary key; unique and required. |
| `name` | Human-readable product name. Required. |
| `unit` | Unit used when counting the product, such as `each`, `bundle`, or `pair`. Required. |

Products has no foreign keys. Inventory references `Products.sku`, so one product can be associated with multiple inventory rows and locations.

## Example rows

| sku | name | unit |
|---|---|---|
| A100 | Canvas Tool Roll | each |
| B205 | Insulated Travel Mug | each |
| C310 | Packing Paper Bundle | bundle |

## Example queries

```sql
SELECT * FROM Products WHERE sku = 'A100';

SELECT sku, name, unit
FROM Products
ORDER BY sku;

SELECT Products.sku, Products.name, Inventory.quantity, Locations.location_id
FROM Products
JOIN Inventory ON Inventory.sku = Products.sku
JOIN Locations ON Locations.location_id = Inventory.location_id
WHERE Products.sku = 'A100';
```

## Questions an eventual warehouse agent could answer

- What product does SKU `A100` identify?
- What unit should be used when counting a product?
- Which SKUs and product names are in the catalog?
- Where is a product stored, when combined with Inventory and Locations?