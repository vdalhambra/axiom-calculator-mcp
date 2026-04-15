"""Mortgage and real estate calculators."""

import math
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP


def register_mortgage_tools(mcp: FastMCP) -> None:

    @mcp.tool(tags={"mortgage", "real-estate"}, annotations={"readOnlyHint": True})
    def mortgage_calculator(
        home_price: Annotated[float, Field(description="Total home price in your currency")],
        down_payment_pct: Annotated[float, Field(description="Down payment percentage (e.g., 20 for 20%)", ge=0, le=100)],
        annual_rate_pct: Annotated[float, Field(description="Annual interest rate percentage (e.g., 3.5 for 3.5%)", ge=0)],
        years: Annotated[int, Field(description="Loan term in years (e.g., 15, 20, 30)", ge=1, le=50)],
        monthly_extras: Annotated[float, Field(description="Additional monthly costs: property tax + insurance + HOA (0 if unknown)", ge=0)] = 0,
    ) -> dict:
        """Calculate monthly mortgage payment, total interest paid, and full amortization summary.

        Returns the monthly principal+interest payment, total interest over the loan life,
        total cost of the home, break-even analysis, and the first 12 months of amortization.
        Optionally includes property tax and insurance in the total monthly cost.
        """
        loan = home_price * (1 - down_payment_pct / 100)
        monthly_rate = annual_rate_pct / 100 / 12
        n = years * 12

        if monthly_rate == 0:
            monthly_pi = loan / n
        else:
            monthly_pi = loan * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)

        total_paid = monthly_pi * n
        total_interest = total_paid - loan
        total_monthly = monthly_pi + monthly_extras

        # First 12 months amortization
        schedule = []
        balance = loan
        for month in range(1, min(13, n + 1)):
            interest_payment = balance * monthly_rate
            principal_payment = monthly_pi - interest_payment
            balance -= principal_payment
            schedule.append({
                "month": month,
                "payment": round(monthly_pi, 2),
                "principal": round(principal_payment, 2),
                "interest": round(interest_payment, 2),
                "balance": round(max(balance, 0), 2),
            })

        return {
            "loan_amount": round(loan, 2),
            "down_payment": round(home_price * down_payment_pct / 100, 2),
            "monthly_principal_interest": round(monthly_pi, 2),
            "monthly_extras": round(monthly_extras, 2),
            "total_monthly_payment": round(total_monthly, 2),
            "total_interest_paid": round(total_interest, 2),
            "total_cost_of_home": round(home_price * down_payment_pct / 100 + total_paid, 2),
            "interest_to_loan_ratio": f"{total_interest / loan * 100:.1f}%",
            "loan_term_years": years,
            "annual_rate": f"{annual_rate_pct}%",
            "first_12_months_amortization": schedule,
            "summary": (
                f"Monthly payment: {monthly_pi:,.2f} (P+I) + {monthly_extras:,.2f} (extras) = {total_monthly:,.2f} total. "
                f"Over {years} years you'll pay {total_interest:,.2f} in interest on a {loan:,.2f} loan "
                f"({total_interest / loan * 100:.1f}% of the loan amount)."
            ),
        }

    @mcp.tool(tags={"mortgage", "real-estate"}, annotations={"readOnlyHint": True})
    def rent_vs_buy(
        home_price: Annotated[float, Field(description="Purchase price of the home")],
        down_payment_pct: Annotated[float, Field(description="Down payment percentage", ge=0, le=100)],
        annual_rate_pct: Annotated[float, Field(description="Mortgage annual interest rate %", ge=0)],
        years: Annotated[int, Field(description="Years of comparison (how long you plan to stay)", ge=1, le=30)],
        monthly_rent: Annotated[float, Field(description="Current monthly rent for equivalent property", ge=0)],
        annual_home_appreciation_pct: Annotated[float, Field(description="Expected annual home value appreciation % (historical avg ~3-4%)", ge=-10, le=20)] = 3.5,
        annual_rent_increase_pct: Annotated[float, Field(description="Expected annual rent increase % (historical avg ~3%)", ge=0, le=20)] = 3.0,
    ) -> dict:
        """Compare total cost of renting vs buying over a given number of years.

        Accounts for mortgage payments, equity built, opportunity cost of down payment,
        rent increases over time, and home appreciation. Returns which option is cheaper
        and by how much over the analysis period.
        """
        loan = home_price * (1 - down_payment_pct / 100)
        dp = home_price * down_payment_pct / 100
        monthly_rate = annual_rate_pct / 100 / 12
        n = years * 12
        total_months = years * 12

        if monthly_rate == 0:
            monthly_pi = loan / (years * 12)
        else:
            monthly_pi = loan * (monthly_rate * (1 + monthly_rate) ** (years * 12)) / ((1 + monthly_rate) ** (years * 12) - 1)

        # Total buying cost
        total_mortgage_paid = monthly_pi * total_months
        home_value_at_end = home_price * (1 + annual_home_appreciation_pct / 100) ** years
        # Remaining balance
        if monthly_rate == 0:
            remaining = loan - monthly_pi * total_months
        else:
            remaining = loan * ((1 + monthly_rate) ** total_months - (1 + monthly_rate) ** total_months) / ((1 + monthly_rate) ** (years * 12) - 1)
            remaining = loan * (1 + monthly_rate) ** total_months - monthly_pi * ((1 + monthly_rate) ** total_months - 1) / monthly_rate
        equity_at_end = home_value_at_end - max(remaining, 0)
        net_buy_cost = dp + total_mortgage_paid - equity_at_end

        # Total renting cost
        total_rent = 0
        current_rent = monthly_rent
        for year in range(years):
            total_rent += current_rent * 12
            current_rent *= (1 + annual_rent_increase_pct / 100)

        # Opportunity cost of down payment (assume 7% annual investment return)
        opportunity_cost = dp * ((1.07 ** years) - 1)

        buy_total_net = net_buy_cost + opportunity_cost
        rent_total = total_rent

        winner = "Buying" if buy_total_net < rent_total else "Renting"
        difference = abs(buy_total_net - rent_total)

        return {
            "analysis_years": years,
            "total_rent_paid": round(total_rent, 2),
            "total_mortgage_paid": round(total_mortgage_paid, 2),
            "down_payment": round(dp, 2),
            "home_value_at_end": round(home_value_at_end, 2),
            "equity_built": round(equity_at_end, 2),
            "opportunity_cost_of_down_payment": round(opportunity_cost, 2),
            "net_cost_of_buying": round(buy_total_net, 2),
            "net_cost_of_renting": round(rent_total, 2),
            "winner": winner,
            "difference": round(difference, 2),
            "summary": (
                f"Over {years} years, {winner.lower()} is cheaper by {difference:,.2f}. "
                f"Buying net cost: {buy_total_net:,.2f} (after equity of {equity_at_end:,.2f}). "
                f"Renting total: {rent_total:,.2f}."
            ),
        }
