# Axiom Calculator MCP

Personal finance calculators for Claude and AI agents — mortgage payments, compound interest, FIRE retirement number, loan comparison, debt payoff, and inflation-adjusted returns.

**Zero API keys. Zero setup. Works instantly with any MCP client.**

[![PyPI](https://img.shields.io/pypi/v/axiom-calculator-mcp)](https://pypi.org/project/axiom-calculator-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Tools (8 total)

| Tool | What it does |
|------|-------------|
| `mortgage_calculator` | Monthly payment, total interest, 12-month amortization schedule |
| `rent_vs_buy` | Compare total cost of renting vs buying over N years (includes equity, appreciation, opportunity cost) |
| `compound_interest` | Project investment growth with optional monthly contributions — year-by-year table |
| `fire_number` | Calculate your FIRE target portfolio and years-to-retirement timeline |
| `inflation_adjusted_return` | Real vs nominal return — see if your investments actually beat inflation |
| `loan_comparison` | Compare two loans by total cost, monthly payment, and true APR (including fees) |
| `true_credit_cost` | Find the real APR of any financing offer, BNPL, or credit product |
| `debt_payoff_plan` | Payoff timeline and interest saved from extra monthly payments |

---

## Install

### Claude Desktop / Claude Code

Add to your MCP config:

```json
{
  "mcpServers": {
    "calculator": {
      "command": "uvx",
      "args": ["axiom-calculator-mcp"]
    }
  }
}
```

### Any MCP client (stdio)

```bash
uvx axiom-calculator-mcp
```

### From source

```bash
git clone https://github.com/vdalhambra/axiom-calculator-mcp
cd axiom-calculator-mcp
uv run axiom-calculator
```

---

## Example usage

Once connected, just ask Claude naturally:

> *"I'm looking at a $450,000 house with 20% down at 6.8% for 30 years. What's my monthly payment and total interest?"*

> *"Compare a 15-year loan at 6.2% vs 30-year at 6.8% for $380,000. Which is better overall?"*

> *"I spend $48,000/year. How much do I need to retire, and how long will it take if I save $24,000/year?"*

> *"I have $8,500 in credit card debt at 22% APR. How long to pay it off at $250/month, and how much do I save if I add $100/month extra?"*

---

## Why this exists

Most finance calculators are either locked behind paywalls, require accounts, or are ad-stuffed websites. This MCP gives Claude direct access to accurate financial math — no API keys, no rate limits, no middleman.

---

## Part of the Axiom MCP suite

- [FinanceKit MCP](https://github.com/vdalhambra/financekit-mcp) — Stock quotes, fundamentals, crypto, insider transactions
- [SiteAudit MCP](https://github.com/vdalhambra/siteaudit-mcp) — SEO audits, Core Web Vitals, backlink analysis

---

## License

MIT — free to use, modify, and distribute.
