"""Tools registered with the WMS agent and its documentation generator."""

from tools.purchase_order import get_PO_list, get_PO_detail, get_all_PO_vendor
from tools.helpers import get_datetime, basic_calculator, calculate_percentage

tools = [
    get_PO_list,
    get_PO_detail,
    get_all_PO_vendor,
    get_datetime,
    basic_calculator,
    calculate_percentage,
]
