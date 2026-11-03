-- INSERT OR IGNORE keeps this small seed script safe to run more than once.
-- All names and quantities below are synthetic learning data.
INSERT OR IGNORE INTO Products (sku, name, unit) VALUES
    ('A100', 'Canvas Tool Roll', 'each'),
    ('B205', 'Insulated Travel Mug', 'each'),
    ('C310', 'Packing Paper Bundle', 'bundle'),
    ('D422', 'LED Work Light', 'each'),
    ('E518', 'Reusable Storage Bin', 'each'),
    ('F630', 'Cotton Work Gloves', 'pair');

INSERT OR IGNORE INTO Locations (location_id, zone, type) VALUES
    ('P-01-01', 'A', 'PICKING'),
    ('P-01-02', 'A', 'PICKING'),
    ('R-02-01', 'B', 'RESERVE'),
    ('R-02-02', 'B', 'RESERVE'),
    ('S-DOCK-01', 'C', 'STAGING'),
    ('RCV-DOCK-01', 'D', 'RECEIVING'),
    ('RCV-DOCK-02', 'D', 'RECEIVING');

-- A SKU may appear in multiple locations; each row records one location balance.
WITH seed_inventory (sku, location_id, quantity, status) AS (
    VALUES
    ('A100', 'P-01-01', 18, 'AVAILABLE'),
    ('A100', 'R-02-01', 72, 'AVAILABLE'),
    ('A100', 'S-DOCK-01', 4, 'HOLD'),
    ('B205', 'P-01-02', 11, 'AVAILABLE'),
    ('B205', 'R-02-02', 36, 'AVAILABLE'),
    ('C310', 'P-01-01', 25, 'AVAILABLE'),
    ('C310', 'RCV-DOCK-01', 12, 'HOLD'),
    ('D422', 'P-01-02', 7, 'AVAILABLE'),
    ('D422', 'R-02-01', 21, 'AVAILABLE'),
    ('E518', 'R-02-02', 15, 'AVAILABLE'),
    ('E518', 'S-DOCK-01', 3, 'HOLD'),
    ('F630', 'RCV-DOCK-02', 40, 'AVAILABLE')
)
INSERT INTO Inventory (sku, location_id, quantity, status)
SELECT seed_inventory.sku, seed_inventory.location_id,
             seed_inventory.quantity, seed_inventory.status
FROM seed_inventory
WHERE NOT EXISTS (
        SELECT 1
        FROM Inventory
        WHERE Inventory.sku = seed_inventory.sku
            AND Inventory.location_id = seed_inventory.location_id
            AND Inventory.quantity = seed_inventory.quantity
            AND Inventory.status = seed_inventory.status
);

INSERT OR IGNORE INTO ShipmentOrders
    (shipment_id, customer, status)
VALUES
    ('SO-1001', 'KK Mart', 'CREATED'),
    ('SO-1002', 'Fresh Market', 'CREATED'),
    ('SO-1003', 'ABC Store', 'CREATED');


WITH seed_shipment_lines (shipment_id, sku, quantity) AS (
    VALUES
    ('SO-1001', 'A100', 50),
    ('SO-1001', 'B205', 25),

    ('SO-1002', 'A100', 100),
    ('SO-1002', 'C310', 15),

    ('SO-1003', 'B205', 5)
)
INSERT INTO ShipmentLines (shipment_id, sku, quantity)
SELECT seed_shipment_lines.shipment_id,
       seed_shipment_lines.sku,
       seed_shipment_lines.quantity
FROM seed_shipment_lines
WHERE NOT EXISTS (
    SELECT 1
    FROM ShipmentLines
    WHERE ShipmentLines.shipment_id = seed_shipment_lines.shipment_id
      AND ShipmentLines.sku = seed_shipment_lines.sku
      AND ShipmentLines.quantity = seed_shipment_lines.quantity
);

-- Allocation plans reserve only AVAILABLE inventory and stay within each
-- inventory row's unallocated quantity. IDs are resolved from the seeded rows.
WITH allocation_plan (
    shipment_id, sku, inventory_location, quantity
) AS (
    VALUES
    ('SO-1001', 'A100', 'P-01-01', 18),
    ('SO-1001', 'A100', 'R-02-01', 32),
    ('SO-1001', 'B205', 'P-01-02', 11),
    ('SO-1001', 'B205', 'R-02-02', 14)
)
INSERT INTO Allocations (
    shipment_line_id, shipment_id, inventory_id, sku, quantity,
    from_location, allocation_rule, allocated, picked, status
)
SELECT sl.shipment_line_id,
       ap.shipment_id,
       i.inventory_id,
       ap.sku,
       ap.quantity,
       ap.inventory_location,
       'PICK_FACE_FIRST',
       1,
       0,
       'ALLOCATED'
FROM allocation_plan AS ap
JOIN ShipmentLines AS sl
  ON sl.shipment_id = ap.shipment_id
 AND sl.sku = ap.sku
JOIN Inventory AS i
  ON i.sku = ap.sku
 AND i.location_id = ap.inventory_location
 AND i.status = 'AVAILABLE'
WHERE NOT EXISTS (
    SELECT 1
    FROM Allocations AS existing
    WHERE existing.shipment_line_id = sl.shipment_line_id
      AND existing.inventory_id = i.inventory_id
)
AND i.quantity - COALESCE((
    SELECT SUM(existing.quantity)
    FROM Allocations AS existing
    WHERE existing.inventory_id = i.inventory_id
), 0) >= ap.quantity;

-- SO-1001 reserves 50 of the 90 available A100 units, leaving 40 for SO-1002.
-- HOLD inventory is excluded, and the remaining demand is intentionally short.
WITH allocation_plan (
    shipment_id, sku, inventory_location, quantity
) AS (
    VALUES
    ('SO-1002', 'A100', 'R-02-01', 40),
    ('SO-1002', 'C310', 'P-01-01', 15)
)
INSERT INTO Allocations (
    shipment_line_id, shipment_id, inventory_id, sku, quantity,
    from_location, allocation_rule, allocated, picked, status
)
SELECT sl.shipment_line_id,
       ap.shipment_id,
       i.inventory_id,
       ap.sku,
       ap.quantity,
       ap.inventory_location,
       'PICK_FACE_FIRST',
       1,
       0,
       'ALLOCATED'
FROM allocation_plan AS ap
JOIN ShipmentLines AS sl
  ON sl.shipment_id = ap.shipment_id
 AND sl.sku = ap.sku
JOIN Inventory AS i
  ON i.sku = ap.sku
 AND i.location_id = ap.inventory_location
 AND i.status = 'AVAILABLE'
WHERE NOT EXISTS (
    SELECT 1
    FROM Allocations AS existing
    WHERE existing.shipment_line_id = sl.shipment_line_id
      AND existing.inventory_id = i.inventory_id
)
AND i.quantity - COALESCE((
    SELECT SUM(existing.quantity)
    FROM Allocations AS existing
    WHERE existing.inventory_id = i.inventory_id
), 0) >= ap.quantity;

WITH allocation_plan (
    shipment_id, sku, inventory_location, quantity
) AS (
    VALUES
    ('SO-1003', 'B205', 'R-02-02', 5)
)
INSERT INTO Allocations (
    shipment_line_id, shipment_id, inventory_id, sku, quantity,
    from_location, allocation_rule, allocated, picked, status
)
SELECT sl.shipment_line_id,
       ap.shipment_id,
       i.inventory_id,
       ap.sku,
       ap.quantity,
       ap.inventory_location,
       'PICK_FACE_FIRST',
       1,
       0,
       'ALLOCATED'
FROM allocation_plan AS ap
JOIN ShipmentLines AS sl
  ON sl.shipment_id = ap.shipment_id
 AND sl.sku = ap.sku
JOIN Inventory AS i
  ON i.sku = ap.sku
 AND i.location_id = ap.inventory_location
 AND i.status = 'AVAILABLE'
WHERE NOT EXISTS (
    SELECT 1
    FROM Allocations AS existing
    WHERE existing.shipment_line_id = sl.shipment_line_id
      AND existing.inventory_id = i.inventory_id
)
AND i.quantity - COALESCE((
    SELECT SUM(existing.quantity)
    FROM Allocations AS existing
    WHERE existing.inventory_id = i.inventory_id
), 0) >= ap.quantity;