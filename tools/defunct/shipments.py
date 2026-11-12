import sqlite3
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_shipment(shipment_id: str):
    """Get a shipment order and its shipment lines."""

    logger.info(
        "Tool called: get_shipment | shipment_id=%s",
        shipment_id
    )

    connection = sqlite3.connect("warehouse.db")
    cursor = connection.cursor()

    # Get shipment header
    cursor.execute(
        """
        SELECT shipment_id, customer, status
        FROM ShipmentOrders
        WHERE shipment_id = ?
        """,
        (shipment_id,)
    )

    shipment = cursor.fetchone()

    if shipment is None:
        connection.close()
        return {"error": "Shipment not found"}

    # Get shipment lines
    cursor.execute(
        """
        SELECT sku, quantity
        FROM ShipmentLines
        WHERE shipment_id = ?
        """,
        (shipment_id,)
    )

    lines = cursor.fetchall()

    connection.close()

    result = {
        "shipment_id": shipment[0],
        "customer": shipment[1],
        "status": shipment[2],
        "lines": [
            {
                "sku": line[0],
                "quantity": line[1]
            }
            for line in lines
        ]
    }

    
    logger.info(
        "Tool result: get_shipment | result=%s",
        result
    )

    return result

@tool
def get_all_shipment_ids():
    """Get all shipment ids"""

    logger.info("Tool called: get_all_shipments")

    connection = sqlite3.connect("warehouse.db")
    cursor = connection.cursor()
    
    cursor.execute(
        """
        SELECT shipment_id
        FROM ShipmentOrders
        """
    )

    lines = cursor.fetchall()
    connection.close()

    shipment_ids = [row[0] for row in lines]
    result = {
        "shipment_ids": shipment_ids
    }
    return result