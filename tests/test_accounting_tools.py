from decimal import Decimal

import pandas as pd

from src.tools.accounting_tools import (
    CalculatorTool,
    SpreadsheetReaderTool,
    InvoiceCalculatorTool,
)


def test_calculator_tool_precision():
    tool = CalculatorTool()
    output = tool.execute("Decimal('1.234') + Decimal('2.001')", precision=3)
    assert output.success
    assert output.result == "3.235"


def test_calculator_rejects_invalid_nodes():
    tool = CalculatorTool()
    failure = tool.execute("Decimal('2') + unknown_var")
    assert not failure.success
    assert "name" in failure.error.lower()


def test_spreadsheet_reader(tmp_path):
    df = pd.DataFrame({"qty": [2, 4], "price": [3.0, 4.5]})
    excel_path = tmp_path / "data.xlsx"
    df.to_excel(excel_path, index=False)

    tool = SpreadsheetReaderTool()
    result = tool.execute(str(excel_path))
    assert result.success
    assert result.result["rows"] == 2
    assert "summary" in result.result


def test_invoice_calculator():
    tool = InvoiceCalculatorTool()
    response = tool.execute(
        line_items=[{"quantity": 2, "unit_price": 10}, {"quantity": 1, "unit_price": 5}],
        tax_rate=0.1,
        discount_rate=0.2,
    )
    assert response.success
    assert Decimal(response.result["total"]) > 0
