import sqlite3
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def get_sku_name(sku: str):
    """Get product name for a specific SKU."""
    logger.info("Tool called: get_sku_name | sku=%s", sku)

    connection = sqlite3.connect("warehouse.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT sku, name
        FROM Products
        WHERE sku = ?
        """,
        (sku,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return f"Product with SKU '{sku}' does not exist."

    return row