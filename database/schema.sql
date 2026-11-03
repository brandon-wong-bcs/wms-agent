-- Products are the catalog records. Their SKU is the stable business key.
CREATE TABLE IF NOT EXISTS Products (
    sku TEXT PRIMARY KEY, -- Primary key: uniquely identifies each product.
    name TEXT NOT NULL,
    unit TEXT NOT NULL
);

-- Locations describe physical or operational areas within the warehouse.
CREATE TABLE IF NOT EXISTS Locations (
    location_id TEXT PRIMARY KEY, -- Primary key: uniquely identifies each location.
    zone TEXT NOT NULL,
    type TEXT NOT NULL
);

-- Inventory connects products to locations and records the quantity and state.
-- The two foreign keys make each inventory row relate to one product and one location.
CREATE TABLE IF NOT EXISTS Inventory (
    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Database-generated row identifier.
    sku TEXT NOT NULL,
    location_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0), -- A stored quantity cannot be negative.
    status TEXT NOT NULL,
    FOREIGN KEY (sku) REFERENCES Products (sku),
    FOREIGN KEY (location_id) REFERENCES Locations (location_id)
);

CREATE TABLE IF NOT EXISTS ShipmentOrders (
    shipment_id TEXT PRIMARY KEY,
    customer TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ShipmentLines (
    shipment_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),

    FOREIGN KEY (shipment_id)
        REFERENCES ShipmentOrders(shipment_id),

    FOREIGN KEY (sku)
        REFERENCES Products(sku)
);

CREATE TABLE IF NOT EXISTS Allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_line_id INTEGER NOT NULL,
    shipment_id TEXT NOT NULL,
    inventory_id INTEGER NOT NULL,
    sku TEXT NOT NULL,
    lpn TEXT,
    quantity INTEGER NOT NULL,
    from_location TEXT NOT NULL,
    to_location TEXT,
    allocation_rule TEXT,
    allocated INTEGER NOT NULL DEFAULT 0,
    picked INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,

    FOREIGN KEY (shipment_line_id)
        REFERENCES ShipmentLines(shipment_line_id),
    FOREIGN KEY (shipment_id)
        REFERENCES ShipmentOrders(shipment_id),
    FOREIGN KEY (inventory_id)
        REFERENCES Inventory(inventory_id),
    FOREIGN KEY (sku)
        REFERENCES Products(sku),
    FOREIGN KEY (from_location)
        REFERENCES Locations(location_id),
    FOREIGN KEY (to_location)
        REFERENCES Locations(location_id)
);