"""Investment and retirement calculators."""

import math
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP


def register_investment_tools(mcp: FastMCP) -> None:

    @mcp.tool(tags={"investment", "compound-interest"}, annotations={"readOnlyHint": True})
    def compound_interest(
        principal: Annotated[float, Field(description="Initial investment amount", ge=0)],
        annual_rate_pct: Annotated[float, Field(description="Expected annual return percentage (e.g., 7 for 7%)")],
        years: Annotated[int, Field(description="Number of years to invest", ge=1, le=100)],
        monthly_contribution: Annotated[float, Field(description="Additional amount added every month (0 for lump sum only)", ge=0)] = 0,
        compounding_frequency: Annotated[str, Field(description="How often interest compounds: 'monthly', 'quarterly', 'annually'")] = "monthly",
    ) -> dict:
        """Project investment growth with compound interest and optional regular contributions.

        Shows final value, total contributions, total interest earned, and a year-by-year
        growth table. Uses the standard compound interest formula with optional periodic contributions.
        """
        freq_map = {"monthly": 12, "quarterly": 4, "annually": 1}
        n = freq_map.get(compounding_frequency.lower(), 12)
        rate_per_period = annual_rate_pct / 100 / n
        total_periods = years * n
        contribution_per_period = monthly_contribution * (12 / n)

        # Future value of lump sum
        fv_lump = principal * (1 + rate_per_period) ** total_periods

        # Future value of periodic contributions
        if rate_per_period == 0:
            fv_contributions = contribution_per_period * total_periods
        else:
            fv_contributions = contribution_per_period * ((1 + rate_per_period) ** total_periods - 1) / rate_per_period

        total_value = fv_lump + fv_contributions
        total_contributed = principal + monthly_contribution * 12 * years
        total_interest = total_value - total_contributed

        # Year-by-year table
        yearly = []
        balance = principal
        for year in range(1, years + 1):
            periods_this_year = n
            for _ in range(periods_this_year):
                balance = balance * (1 + rate_per_period) + contribution_per_period
            yearly.append({
                "year": year,
                "balance": round(balance, 2),
                "total_contributed": round(principal + monthly_contribution * 12 * year, 2),
                "gains": round(balance - (principal + monthly_contribution * 12 * year), 2),
            })

        return {
            "initial_investment": principal,
            "monthly_contribution": monthly_contribution,
            "annual_return": f"{annual_rate_pct}%",
            "years": years,
            "compounding": compounding_frequency,
            "final_value": round(total_value, 2),
            "total_contributed": round(total_contributed, 2),
            "total_interest_earned": round(total_interest, 2),
            "return_on_investment": f"{(total_interest / total_contributed * 100):.1f}%" if total_contributed > 0 else "0%",
            "money_doubled": f"Doubles every {72 / annual_rate_pct:.1f} years (Rule of 72)" if annual_rate_pct > 0 else "N/A",
            "yearly_growth": yearly,
            "summary": (
                f"Starting with {principal:,.2f} and adding {monthly_contribution:,.2f}/month at {annual_rate_pct}% annual return, "
                f"after {years} years you'll have {total_value:,.2f}. "
                f"You contributed {total_contributed:,.2f} and earned {total_interest:,.2f} in interest "
                f"({total_interest / total_contributed * 100:.1f}% return on contributions)."
            ),
        }

    @mcp.tool(tags={"retirement", "fire"}, annotations={"readOnlyHint": True})
    def fire_number(
        annual_expenses: Annotated[float, Field(description="Your current annual living expenses", gt=0)],
        withdrawal_rate_pct: Annotated[float, Field(description="Safe withdrawal rate % (4% is the classic 'Rule of 4%', 3.5% is conservative)", ge=1, le=10)] = 4.0,
        current_savings: Annotated[float, Field(description="Current investment portfolio value (0 if starting from zero)", ge=0)] = 0,
        annual_savings: Annotated[float, Field(description="Amount you save/invest per year currently", ge=0)] = 0,
        expected_return_pct: Annotated[float, Field(description="Expected annual portfolio return % (7% is common for diversified index funds)", ge=0)] = 7.0,
        inflation_pct: Annotated[float, Field(description="Expected annual inflation % (3% is typical)", ge=0)] = 3.0,
    ) -> dict:
        """Calculate your FIRE (Financial Independence, Retire Early) number and timeline.

        Finds the portfolio size needed to cover your expenses indefinitely using the
        chosen withdrawal rate. If you provide current savings and annual savings rate,
        also estimates how many years until you reach FIRE.
        """
        fire_target = annual_expenses / (withdrawal_rate_pct / 100)
        real_return = (1 + expected_return_pct / 100) / (1 + inflation_pct / 100) - 1

        # Years to FIRE
        years_to_fire = None
        yearly_path = []
        if annual_savings > 0 or current_savings > 0:
            balance = current_savings
            monthly_savings = annual_savings / 12
            monthly_rate = expected_return_pct / 100 / 12
            for month in range(1, 601):  # max 50 years
                balance = balance * (1 + monthly_rate) + monthly_savings
                if month % 12 == 0:
                    year = month // 12
                    yearly_path.append({"year": year, "portfolio": round(balance, 2), "target": round(fire_target, 2), "pct_of_target": f"{balance / fire_target * 100:.1f}%"})
                    if balance >= fire_target and years_to_fire is None:
                        years_to_fire = year

        # Monthly passive income at FIRE
        monthly_passive = annual_expenses / 12

        return {
            "annual_expenses": annual_expenses,
            "withdrawal_rate": f"{withdrawal_rate_pct}%",
            "fire_number": round(fire_target, 2),
            "monthly_passive_income_at_fire": round(monthly_passive, 2),
            "current_savings": current_savings,
            "annual_savings": annual_savings,
            "gap_to_fire": round(max(fire_target - current_savings, 0), 2),
            "years_to_fire": years_to_fire,
            "yearly_path": yearly_path[:20] if yearly_path else [],  # first 20 years
            "fire_variants": {
                "lean_fire_4pct": round(annual_expenses / 0.04, 2),
                "fat_fire_3pct": round(annual_expenses / 0.03, 2),
                "coast_fire_note": "Coast FIRE = stop contributing now and let compound interest reach the target",
            },
            "summary": (
                f"At {withdrawal_rate_pct}% withdrawal rate, you need {fire_target:,.2f} to cover {annual_expenses:,.2f}/year in expenses. "
                + (f"At your current savings rate, you'll reach FIRE in approximately {years_to_fire} years." if years_to_fire else "Add your annual savings to estimate timeline.")
            ),
        }

    @mcp.tool(tags={"investment", "inflation"}, annotations={"readOnlyHint": True})
    def inflation_adjusted_return(
        nominal_return_pct: Annotated[float, Field(description="Nominal annual return percentage (e.g., 10 for 10%)")],
        inflation_rate_pct: Annotated[float, Field(description="Annual inflation rate percentage (e.g., 3 for 3%)")],
        years: Annotated[int, Field(description="Number of years", ge=1, le=50)],
        initial_amount: Annotated[float, Field(description="Initial investment amount", ge=0)] = 10000,
    ) -> dict:
        """Calculate the real (inflation-adjusted) return on an investment.

        Shows the difference between nominal growth and actual purchasing power growth.
        Useful for understanding if your investments are truly beating inflation.
        """
        real_return = (1 + nominal_return_pct / 100) / (1 + inflation_rate_pct / 100) - 1
        nominal_value = initial_amount * (1 + nominal_return_pct / 100) ** years
        real_value = initial_amount * (1 + real_return) ** years
        purchasing_power_lost = nominal_value - real_value

        return {
            "initial_amount": initial_amount,
            "years": years,
            "nominal_return": f"{nominal_return_pct}%",
            "inflation_rate": f"{inflation_rate_pct}%",
            "real_return": f"{real_return * 100:.2f}%",
            "nominal_final_value": round(nominal_value, 2),
            "real_final_value_today_dollars": round(real_value, 2),
            "purchasing_power_eroded": round(purchasing_power_lost, 2),
            "beats_inflation": real_return > 0,
            "summary": (
                f"Your {nominal_return_pct}% nominal return minus {inflation_rate_pct}% inflation gives a real return of {real_return * 100:.2f}%. "
                f"In today's purchasing power, {initial_amount:,.2f} grows to {real_value:,.2f} (not {nominal_value:,.2f} nominally). "
                + ("Your investment beats inflation." if real_return > 0 else "WARNING: Your investment does NOT beat inflation — you are losing purchasing power.")
            ),
        }
