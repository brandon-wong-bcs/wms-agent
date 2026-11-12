import sqlite3
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_location(location_id: str):
    """Get location details for a specific warehouse location ID."""
    logger.info("Tool called: get_location | location_id=%s", location_id)

    connection = sqlite3.connect("warehouse.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT location_id, zone, type
        FROM Locations
        WHERE location_id = ?
        """,
        (location_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    return rows