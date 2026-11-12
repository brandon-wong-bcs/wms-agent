import os
import logging
from langchain_core.tools import tool
from agent.wms_client import call_wms, pick

#logger = logging.getLogger(__name__)
#logger.info("Tool called: get_inventory | sku=%s", sku)

WAREHOUSE = os.environ["WMS_WAREHOUSE"]
INVENTORY_FIELDS = [
    "inventoryId",
    "companyCode",
    "sku",
    "skuFullName",
    "itemDescription",
    "location",
    "lpn",
    "onHandQuantity",
    "inTransitQuantity",
    "allocatedQuantity",
    "suspendedQuantity",
    "availableQuantity",
    "quantityUnit",
    "inventoryStatus",
    "lot01",
    "receivedDate",
    "expiryDate",
    "locationGroup",
    "locationType",
    "locationArea",
    "locationZone",
]

@tool
def get_inventory(
    sku: str = "",
    location: str = "",
    lpn: str = "",
) -> dict:
    """
    Look up current WMS inventory.

    Use this tool when the user asks about inventory for a specific
    SKU, location, or LPN.

    At least one of sku, location, or lpn must be provided.
    """

    # Don't allow the agent to accidentally request the entire warehouse.
    if not sku and not location and not lpn:
        return {
            "error": "A SKU, location, or LPN is required."
        }

    data = call_wms(
        "/api/app/inventory",
        {
            "WarehouseCode": WAREHOUSE,
            "Sku": sku,
            "Location": location,
            "Lpn": lpn,
            "MaxResultCount": 25,
        },
    )

    items = data.get("items", [])
    total_count = data.get("totalCount")

    return {
        "rows": [
            pick(item, INVENTORY_FIELDS)
            for item in items
        ],
        "returnedRows": len(items),
        "totalCount": total_count,
        "partial": (
            total_count is None
            or total_count > len(items)
        ),
    }
