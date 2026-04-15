"""
Axiom Calculator MCP — Personal Finance Calculators for AI Agents.

Mortgage payments, compound interest, FIRE number, loan comparison,
inflation-adjusted returns, and true credit cost. Zero external dependencies.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastmcp import FastMCP
from calculator.tools.mortgage import register_mortgage_tools
from calculator.tools.investment import register_investment_tools
from calculator.tools.loans import register_loan_tools

mcp = FastMCP(
    name="Axiom Calculator",
    instructions=(
        "Personal finance calculator with zero external dependencies. "
        "Use these tools to calculate mortgage payments and amortization, "
        "project compound interest growth, find your FIRE (Financial Independence) number, "
        "compare loans by true cost, calculate inflation-adjusted returns, "
        "and find the real APR of credit products. "
        "All calculations are done locally — no API keys required. "
        "Results include step-by-step breakdowns and plain-language explanations."
    ),
    version="1.0.0",
)

register_mortgage_tools(mcp)
register_investment_tools(mcp)
register_loan_tools(mcp)


def main():
    import os
    if os.environ.get("PORT"):
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ["PORT"]))
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
