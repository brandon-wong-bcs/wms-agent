# WMS Agent Tools

## `get_PO_list`

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

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `purchaseOrderNo` | string | No |  |
| `vendor` | string | No |  |
| `sku` | string | No |  |
| `status` | string | No |  |
| `purchaseOrderTypeCode` | string | No |  |
| `dateFrom` | string | No |  |
| `dateTo` | string | No |  |
| `includeClosed` | boolean | No |  |

## `get_PO_detail`

Retrieve detailed information for a single purchase order in the WMS.

Use this tool when information about the individual lines of a purchase
order is required, such as SKUs, quantities, UOMs, costs, or line statuses.

This tool requires the PO header ID returned by get_PO_list.
If the PO header ID is not known, use get_PO_list first to locate the
purchase order and obtain its PO header ID.

Returns the purchase order header and its individual purchase order lines

This tool retrieves a single purchase order's details only and does not search for purchase orders

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `poHeaderId` | integer | Yes |  |

## `get_all_PO_vendor`

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

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `search` | string | No |  |
| `skipCount` | integer | No |  |

## `get_datetime`

Get the current local date and time.

### Parameters

This tool has no parameters.

## `basic_calculator`

Perform basic arithmetic: add, subtract, multiply, or divide.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `a` | number | Yes |  |
| `b` | number | Yes |  |
| `operation` | string | Yes |  |

## `calculate_percentage`

Calculate what percentage part represents of total.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `part` | number | Yes |  |
| `total` | number | Yes |  |
