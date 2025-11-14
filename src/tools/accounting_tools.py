"""
Tools for accounting and financial tasks.
"""
from __future__ import annotations

import ast
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
import pandas as pd
from .base import BaseTool, ToolCategory, ToolOutput


class _SafeDecimalEvaluator(ast.NodeVisitor):
    """Safely evaluate mathematical expressions using :class:`Decimal`."""

    _BINARY_OPERATORS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        ast.Pow: lambda a, b: a ** b,
    }

    _UNARY_OPERATORS = {
        ast.UAdd: lambda a: a,
        ast.USub: lambda a: -a,
    }

    def visit(self, node: ast.AST) -> Decimal:
        value = super().visit(node)
        if not isinstance(value, Decimal):
            return Decimal(value)
        return value

    def visit_Expression(self, node: ast.Expression) -> Decimal:
        return self.visit(node.body)

    def visit_BinOp(self, node: ast.BinOp) -> Decimal:
        operator_type = type(node.op)
        if operator_type not in self._BINARY_OPERATORS:
            raise ValueError(f"Operator '{operator_type.__name__}' is not allowed")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self._BINARY_OPERATORS[operator_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Decimal:
        operator_type = type(node.op)
        if operator_type not in self._UNARY_OPERATORS:
            raise ValueError(f"Unary operator '{operator_type.__name__}' is not allowed")
        operand = self.visit(node.operand)
        return self._UNARY_OPERATORS[operator_type](operand)

    def visit_Call(self, node: ast.Call) -> Decimal:
        if not isinstance(node.func, ast.Name) or node.func.id != "Decimal":
            raise ValueError("Only Decimal() calls are permitted")
        if len(node.args) != 1 or node.keywords:
            raise ValueError("Decimal() expects a single positional argument")
        arg_value = self.visit(node.args[0])
        return Decimal(arg_value)

    def visit_Name(self, node: ast.Name) -> Decimal:
        raise ValueError(f"Usage of name '{node.id}' is not permitted")

    def visit_Constant(self, node: ast.Constant) -> Decimal:
        if isinstance(node.value, (int, float, Decimal)):
            return Decimal(str(node.value))
        if isinstance(node.value, str):
            return Decimal(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    def generic_visit(self, node):
        raise ValueError(f"Unsupported expression component: {type(node).__name__}")


def _evaluate_decimal_expression(expression: str) -> Decimal:
    """Parse and safely evaluate an arithmetic expression to a Decimal."""
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression: {exc.msg}") from exc

    evaluator = _SafeDecimalEvaluator()
    return evaluator.visit(parsed)


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
            result = _evaluate_decimal_expression(expression)
            quantized = result.quantize(
                Decimal(10) ** -precision,
                rounding=ROUND_HALF_UP
            )

            return ToolOutput(
                success=True,
                result=str(quantized),
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
        sheet_name: str | int | None = None,
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
            # pandas interprets sheet_name=None as "all sheets" which returns a dict;
            # we want the first sheet by default for predictable structure.
            resolved_sheet = 0 if sheet_name is None else sheet_name
            df = pd.read_excel(file_path, sheet_name=resolved_sheet, header=header_row)

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
