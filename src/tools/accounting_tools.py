"""
Tools for accounting and financial tasks.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
import pandas as pd
from .base import BaseTool, ToolCategory, ToolOutput


class CalculatorTool(BaseTool):
    """Perform financial calculations with high precision."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ACCOUNTING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only calculation

    def execute(self, expression: str, precision: int = 2) -> ToolOutput:
        """
        Evaluate a mathematical expression with decimal precision.

        Args:
            expression: Mathematical expression to evaluate
            precision: Decimal precision

        Returns:
            ToolOutput with calculation result
        """
        try:
            # Use Decimal for precision
            result = eval(expression, {"Decimal": Decimal, "__builtins__": {}})

            if isinstance(result, Decimal):
                result = result.quantize(
                    Decimal(10) ** -precision,
                    rounding=ROUND_HALF_UP
                )

            return ToolOutput(
                success=True,
                result=str(result),
                metadata={"expression": expression, "precision": precision}
            )
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class SpreadsheetReaderTool(BaseTool):
    """Read data from Excel spreadsheets."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ACCOUNTING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(
        self,
        file_path: str,
        sheet_name: str = None,
        header_row: int = 0
    ) -> ToolOutput:
        """
        Read data from an Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name (None for first sheet)
            header_row: Row number to use as header

        Returns:
            ToolOutput with spreadsheet data
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)

            result = {
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.to_dict(orient='records'),
                "summary": df.describe().to_dict() if df.select_dtypes(include='number').shape[1] > 0 else None
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class InvoiceCalculatorTool(BaseTool):
    """Calculate invoice totals with tax."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ACCOUNTING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only calculation

    def execute(
        self,
        line_items: List[Dict[str, Any]],
        tax_rate: float = 0.0,
        discount_rate: float = 0.0
    ) -> ToolOutput:
        """
        Calculate invoice total.

        Args:
            line_items: List of items with 'quantity' and 'unit_price'
            tax_rate: Tax rate as decimal (e.g., 0.08 for 8%)
            discount_rate: Discount rate as decimal

        Returns:
            ToolOutput with invoice calculations
        """
        try:
            subtotal = Decimal('0')

            for item in line_items:
                quantity = Decimal(str(item.get('quantity', 0)))
                unit_price = Decimal(str(item.get('unit_price', 0)))
                subtotal += quantity * unit_price

            discount_amount = subtotal * Decimal(str(discount_rate))
            subtotal_after_discount = subtotal - discount_amount
            tax_amount = subtotal_after_discount * Decimal(str(tax_rate))
            total = subtotal_after_discount + tax_amount

            # Round to 2 decimal places
            result = {
                "subtotal": str(subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "discount_rate": discount_rate,
                "discount_amount": str(discount_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "subtotal_after_discount": str(subtotal_after_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "tax_rate": tax_rate,
                "tax_amount": str(tax_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "total": str(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "item_count": len(line_items)
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))
