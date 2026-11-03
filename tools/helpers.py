import logging
import datetime
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_datetime():
    """Get the current local date and time."""
    logger.info("Tool called: get_datetime")
    return datetime.datetime.now().isoformat()

@tool
def basic_calculator(a: float, b: float, operation: str):
    """Perform basic arithmetic: add, subtract, multiply, or divide."""
    logger.info("Tool called: calculator | a=%s | b=%s | operation=%s", a, b, operation)
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            return "Cannot divide by zero."
        return a / b
    return "Unsupported operation."

@tool
def calculate_percentage(part: float, total: float) -> float:
    """Calculate what percentage part represents of total."""

    logger.info(
        "Tool called: calculate_percentage | part=%s | total=%s",
        part,
        total
    )

    if total == 0:
        raise ValueError("Total cannot be zero.")

    return round((part / total) * 100, 2)