import os
import logging

from langchain_core.tools import tool

from agent.wms_client import call_wms, pick
from fields.receipt import RECEIPT_FIELDS, RECEIPT_LINE_FIELDS, RECEIPT_CONTAINER_FIELDS

logger = logging.getLogger(__name__)

WAREHOUSE = os.environ["WMS_WAREHOUSE"]

@tool
def get_Receipt_List(
    receiptNo: str = ""
    poNo: str = ""
    hostHeaderNo: str = ""
    receiptStatus: str = ""
    vendorCode: str = ""
    dateFrom: str = ""
    dateTo: str = ""
    includeCompleted: bool = False
) -> dict:
    """
    Search for receipts in the WMS

    Use this tool when the user wants to find or list receipts using one or more of the following:
    - receipt number
    - purchase order number
    - host header number 
    - receipt status code
    - vendor code
    - receipt creation date range
    - whether completed and cancelled receipts should be included

    Multiple filters can be applied to narrow search

    Returns one or more matching receipt headers.
    This tool returns header-level information and does not return individual receipt line details.

    At least one search filter must be provided
    """

    logger.info(
        "get_Receipt_List called: "
        "receiptNo=%r poNo=%r hostHeaderNo=%r receiptStatus=%r "
        "vendorCode=%r dateFrom=%r dateTo=%r includeCompleted=%r",
        receiptNo,
        poNo,
        hostHeaderNo,
        receiptStatus,
        vendorCode,
        dateFrom,
        dateTo,
        includeCompleted,
    )

    if not any([
        receiptNo,
        poNo,
        hostHeaderNo,
        receiptStatus,
        vendorCode,
        dateFrom,
        dateTo,
        includeCompleted,
    ]):
        return {
            "error": "At least one receipt filter is required."
        }
    
    data = call_wms(
        "/api/app/receipt",
        {
            "WarehouseCode": WAREHOUSE,
            "ReceiptNo": receiptNo,
            "PoNo": poNo,
            "HostHeaderNo": hostHeaderNo,
            "ReceiptStatus": receiptStatus,
            "VendorCode": vendorCode,
            "CreatedFrom": dateFrom,
            "CreatedTo": dateTo,
            "IncludeCompleted": includeCompleted,
            "MaxResultCount": 25,
        },
    )

    # return object