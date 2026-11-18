import os
import logging

from langchain_core.tools import tool

from agent.wms_client import call_wms, pick
from fields.receipt import RECEIPT_FIELDS, RECEIPT_LINE_FIELDS, RECEIPT_CONTAINER_FIELDS

logger = logging.getLogger(__name__)

WAREHOUSE = os.environ["WMS_WAREHOUSE"]

@tool
def get_receipt_list(
    receiptNo: str = "",
    poNo: str = "",
    hostHeaderNo: str = "",
    receiptStatus: str = "",
    vendorCode: str = "",
    dateFrom: str = "",
    dateTo: str = "",
    includeCompleted: bool = False,
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
        "get_receipt_list called: "
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

    items = data.get("items", [])
    total_count = data.get("totalCount")

    return {
        "rows": [
            pick(item, RECEIPT_FIELDS)
            for item in items
        ],
        "returnedRows": len(items),
        "totalCount": total_count,
    }

@tool
def get_receipt_detail(
    receiptNo: str,
    skipCount: int = 0
) -> dict:
# /api/app/receipt/detail-list
    """
    Retrieve detailed line information for a single receipt in the WMS.

    Use this tool for receipt item details, including product and LPN
    information, quantities and units, inventory and putaway information,
    lot attributes, dates, and receiving restrictions.

    Requires the receipt number (for example REC26072800006). Do not call
    get_receipt_list first for a known receipt number.
    skipCount is the number of lines to skip for paging. Use 0 for the
    first page, then the returned nextSkipCount.

    Returns the receipt's lines in items, plus totalCount, hasMore and
    nextSkipCount. This endpoint does not return a receipt header.

    This tool retrieves a single receipt's lines only and does not search
    for receipts.
    """
    
    logger.info(
        "get_receipt_detail called: receiptNo = %r, skipCount = %r",
        receiptNo,
        skipCount,
    )

    receiptNo = receiptNo.strip()
    if not receiptNo:
        return {"error": "A receipt number is required."}
    if skipCount < 0:
        return {"error": "skipCount cannot be negative."}

    found = call_wms(
        "/api/app/receipt",
        {
            "WarehouseCode": WAREHOUSE,
            "ReceiptNo": receiptNo,
            "IncludeCompleted": True,
            "MaxResultCount": 5,
        },
    )
    matches = [
        r for r in found.get("items", [])
        if r.get("receiptNo") == receiptNo
    ]
    if len(matches) != 1:
        return {"error": f"{len(matches)} receipts matched '{receiptNo}'. Ask the user to confirm the receipt number."}
    header_id = matches[0]["receiptHeaderId"]

    data = call_wms(
        "/api/app/receipt/detail-list",
        {
            "ReceiptHeaderId": header_id,
            "SkipCount": skipCount,
        },
    )

    items = data.get("items", [])
    total_count = data.get("totalCount")
    has_more = (
        skipCount + len(items) < total_count
        if total_count is not None
        else None
    )

    if not items and has_more:
        return {
            "error": "Receipt API returned an empty page before the reported total was reached."
        }

    return {
        "receiptNo": receiptNo,
        "items": [pick(item, RECEIPT_LINE_FIELDS) for item in items],
        "totalCount": total_count,
        "hasMore": has_more,
        "nextSkipCount": (
            skipCount + len(items)
            if has_more
            else None
        ),
    }

@tool
def get_receipt_container(
    receiptNo: str,
    skipCount: int = 0
) -> dict:
# /api/app/receipt/container-list
    """
    Retrieve the containers (LPNs) already received against a single receipt
    in the WMS.

    Use this tool for what has actually been received: LPN, SKU, received
    quantity and unit, container and inventory status, putaway location,
    lot attributes, received and expiry dates, and cost. For what is expected
    to be received, use get_receipt_detail instead.

    Requires the receipt number (for example REC26072800006). Do not call
    get_receipt_list first for a known receipt number.
    skipCount is the number of containers to skip for paging. Use 0 for the
    first page, then the returned nextSkipCount.

    Returns the receipt's containers in items, plus totalCount, hasMore and
    nextSkipCount. This endpoint does not return a receipt header.

    This tool retrieves a single receipt's containers only and does not
    search for receipts.
    """

    logger.info(
        "get_receipt_container called: receiptNo = %r, skipCount = %r",
        receiptNo,
        skipCount,
    )

    receiptNo = receiptNo.strip()
    if not receiptNo:
        return {"error": "A receipt number is required."}
    if skipCount < 0:
        return {"error": "skipCount cannot be negative."}

    found = call_wms(
        "/api/app/receipt",
        {
            "WarehouseCode": WAREHOUSE,
            "ReceiptNo": receiptNo,
            "IncludeCompleted": True,
            "MaxResultCount": 5,
        },
    )

    matches = [
        r for r in found.get("items", [])
        if r.get("receiptNo") == receiptNo
    ]
    if len(matches) != 1:
        return {"error": f"{len(matches)} receipts matched '{receiptNo}'. Ask the user to confirm the receipt number."}
    header_id = matches[0]["receiptHeaderId"]

    data = call_wms(
        "/api/app/receipt/container-list",
        {
            "ReceiptHeaderId": header_id,
            "SkipCount": skipCount,
        },
    )

    items = data.get("items", [])
    total_count = data.get("totalCount")
    has_more = (
        skipCount + len(items) < total_count
        if total_count is not None
        else None
    )

    if not items and has_more:
        return {
            "error": "Receipt API returned an empty page before the reported total was reached."
        }

    return {
        "receiptNo": receiptNo,
        "items": [pick(item, RECEIPT_CONTAINER_FIELDS) for item in items],
        "totalCount": total_count,
        "hasMore": has_more,
        "nextSkipCount": (
            skipCount + len(items)
            if has_more
            else None
        ),
    }