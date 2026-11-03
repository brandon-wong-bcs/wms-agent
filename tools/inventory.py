import sqlite3
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_inventory(sku: str):
    """Get warehouse inventory for a specific SKU."""
    logger.info("Tool called: get_inventory | sku=%s", sku)

    connection = sqlite3.connect("warehouse.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT sku, location_id, quantity, status
        FROM Inventory
        WHERE sku = ?
        """,
        (sku,)
    )

    rows = cursor.fetchall()

    connection.close()

    return rows