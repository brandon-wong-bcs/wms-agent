import sqlite3
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def get_allocation(shipment_id: str):
    """Get allocation records for a shipment."""
    logger.info("Tool called: get_allocation | shipment_id=%s", shipment_id)

    connection = sqlite3.connect("warehouse.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            allocation_id,
            shipment_line_id,
            inventory_id,
            sku,
            quantity,
            from_location,
            to_location,
            allocation_rule,
            allocated,
            picked,
            status
        FROM Allocations
        WHERE shipment_id = ?
        """,
        (shipment_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    allocations = [dict(row) for row in rows]

    return {
        "shipment_id": shipment_id,
        "allocations": allocations
    }