import os
import logging

from langchain_core.tools import tool

from agent.wms_client import call_wms, pick
from fields.purchase_order import PO_FIELDS, PO_LINE_FIELDS, PO_VENDOR_FIELDS

logger = logging.getLogger(__name__)

WAREHOUSE = os.environ["WMS_WAREHOUSE"]
COMPANY = os.environ["WMS_COMPANY"]

@tool
def get_PO_list(
    purchaseOrderNo: str = "",
    vendor: str = "",
    sku: str = "",
    status: str = "",
    purchaseOrderTypeCode: str = "",
    dateFrom: str = "",
    dateTo: str = "",
    includeClosed: bool = False
) -> dict:
    """
    Search for purchase orders in the WMS

    Use this tool when the user wants to find or list purchase orders using one or more of the following:
    - purchase order number
    - vendor name
    - sku 
    - purchase order status
    - purchase order type code
    - purchase order date range
    - whether closed purchase orders should be included

    Multiple filters can be applied to narrow search

    Returns one or more matching purchase order headers.
    This tool returns header-level information and does not return individual purchase order line details.

    At least one search filter must be provided
    """

    logger.info(
        "get_PO_list called: "
        "purchaseOrderNo=%r vendor=%r sku=%r status=%r "
        "purchaseOrderTypeCode=%r dateFrom=%r dateTo=%r includeClosed=%r",
        purchaseOrderNo,
        vendor,
        sku,
        status,
        purchaseOrderTypeCode,
        dateFrom,
        dateTo,
        includeClosed,
    )

    if not any([
        purchaseOrderNo,
        vendor,
        sku,
        status,
        purchaseOrderTypeCode,
        dateFrom,
        dateTo,
    ]):
        return {
            "error": "At least one PO filter is required."
        }


    data = call_wms(
        "/api/app/purchase-order",
        {
            "WarehouseCode": WAREHOUSE,
            "PurchaseOrderNo": purchaseOrderNo,
            "Vendor": vendor,
            "Sku": sku,
            "Status": status,
            "PurchaseOrderTypeCode": purchaseOrderTypeCode,
            "DateFrom": dateFrom,
            "DateTo": dateTo,
            "IncludeClosed": includeClosed,
            "MaxResultCount": 25,
        },
    )

    items = data.get("items", [])
    total_count = data.get("totalCount")
    has_more = data.get("hasMore", False)

    return {
        "rows": [
            pick(item, PO_FIELDS)
            for item in items
        ],
        "returnedRows": len(items),
        "totalCount": total_count,
        "hasMore": has_more,
    }

@tool
def get_PO_detail(
    poHeaderId: int
) -> dict:
    """
    Retrieve detailed information for a single purchase order in the WMS.

    Use this tool when information about the individual lines of a purchase
    order is required, such as SKUs, quantities, UOMs, costs, or line statuses.

    This tool requires the PO header ID returned by get_PO_list.
    If the PO header ID is not known, use get_PO_list first to locate the
    purchase order and obtain its PO header ID.

    Returns the purchase order header and its individual purchase order lines

    This tool retrieves a single purchase order's details only and does not search for purchase orders
    """

    logger.info(
        "get_PO_detail called: poHeaderId = %r",
        poHeaderId
    )

    if poHeaderId <= 0:
        return {
            "error": "A valid PO header ID is required."
        }

    data = call_wms(
        f"/api/app/purchase-order/{poHeaderId}",
        {
            "warehouseCode": WAREHOUSE,
            "lineSkipCount": 0,
            "lineMaxResultCount": 100,
        },
    )
    
    header = data.get("header", {})
    lines = data.get("lines", [])
    has_more_lines = data.get("hasMoreLines", False)

    return {
        "header": pick(header, PO_FIELDS),

        "lines": [
            pick(line, PO_LINE_FIELDS)
            for line in lines
        ],

        "returnedLines": len(lines),
        "hasMoreLines": has_more_lines,
    }

@tool
def get_all_PO_vendor(
    search: str = "",
    skipCount: int = 0,
) -> dict:
    """
    Search for purchase order vendors in the WMS.

    Use this tool when the user wants to find or list vendors for purchase orders.

    Use search to filter vendors.

    Results are returned in batches of up to 20 vendors. Do not automatically retrieve
    additional batches, even when more vendors may be available.

    Only retrieve the next batch when the user explicitly asks for more,
    such as "next 20" or "show more". When continuing a previous search,
    preserve the original search value and use the nextSkipCount returned
    by the previous call.

    Returns matching vendor codes and vendor names.

    This tool returns vendor information only and does not return purchase
    orders or purchase order line details.
    """

    logger.info(
        "get_all_PO_vendor called: skipCount = %r, search term = %r",
        skipCount, 
        search
    )

    if skipCount < 0:
        return {
            "error": "skipCount cannot be negative."
        }
    MAX_RESULT_COUNT = 20

    data = call_wms(
        "/api/app/agent-tool/purchase-order-vendors",
        {
            "warehouseCode": WAREHOUSE,
            "companyCode": COMPANY,
            "search": search,
            "skipCount": skipCount,
            "maxResultCount": MAX_RESULT_COUNT,
        },
    )
    
    items = data.get("items", [])
    has_more = data.get("hasMore", False)
    return {
        "vendors": [
            pick(vendor, PO_VENDOR_FIELDS)
            for vendor in items
        ],
        "totalCount": data.get("totalCount", 0),
        "hasMore": has_more,
        "nextSkipCount": (
            skipCount + len(items)
            if has_more
            else None
        ),
    }