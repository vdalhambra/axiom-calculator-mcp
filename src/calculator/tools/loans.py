"""Loan and credit calculators."""

import math
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP


def register_loan_tools(mcp: FastMCP) -> None:

    @mcp.tool(tags={"loans", "credit"}, annotations={"readOnlyHint": True})
    def loan_comparison(
        loan_amount: Annotated[float, Field(description="Amount to borrow", gt=0)],
        option_a_rate_pct: Annotated[float, Field(description="Annual interest rate for option A (%)", ge=0)],
        option_a_years: Annotated[int, Field(description="Loan term for option A in years", ge=1, le=40)],
        option_b_rate_pct: Annotated[float, Field(description="Annual interest rate for option B (%)", ge=0)],
        option_b_years: Annotated[int, Field(description="Loan term for option B in years", ge=1, le=40)],
        option_a_fees: Annotated[float, Field(description="Upfront fees for option A (origination, closing costs, etc.)", ge=0)] = 0,
        option_b_fees: Annotated[float, Field(description="Upfront fees for option B", ge=0)] = 0,
    ) -> dict:
        """Compare two loan options by total cost, monthly payment, and true APR.

        Helps decide between a lower rate with higher fees vs higher rate with lower fees,
        or shorter term (higher payment, less interest) vs longer term (lower payment, more interest).
        """
        def calc_loan(amount, rate_pct, years, fees):
            monthly_rate = rate_pct / 100 / 12
            n = years * 12
            if monthly_rate == 0:
                payment = amount / n
            else:
                payment = amount * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
            total_paid = payment * n
            total_interest = total_paid - amount
            total_cost = total_paid + fees
            # Approximate APR including fees
            if fees > 0:
                effective_amount = amount - fees
                if monthly_rate == 0:
                    apr = 0
                else:
                    # Newton's method to find APR
                    apr_rate = monthly_rate
                    for _ in range(100):
                        f = effective_amount - payment * (1 - (1 + apr_rate) ** -n) / apr_rate
                        df = payment * ((1 - (1 + apr_rate) ** -n) / apr_rate ** 2 - n * (1 + apr_rate) ** (-n - 1) / apr_rate)
                        apr_rate = apr_rate - f / df if df != 0 else apr_rate
                    apr = apr_rate * 12 * 100
            else:
                apr = rate_pct
            return {
                "monthly_payment": round(payment, 2),
                "total_interest": round(total_interest, 2),
                "total_paid": round(total_paid, 2),
                "upfront_fees": fees,
                "total_cost": round(total_cost, 2),
                "true_apr": round(apr, 3),
            }

        a = calc_loan(loan_amount, option_a_rate_pct, option_a_years, option_a_fees)
        b = calc_loan(loan_amount, option_b_rate_pct, option_b_years, option_b_fees)

        better = "A" if a["total_cost"] < b["total_cost"] else "B"
        savings = abs(a["total_cost"] - b["total_cost"])

        return {
            "loan_amount": loan_amount,
            "option_a": {**a, "rate": f"{option_a_rate_pct}%", "term": f"{option_a_years} years"},
            "option_b": {**b, "rate": f"{option_b_rate_pct}%", "term": f"{option_b_years} years"},
            "recommendation": f"Option {better} is cheaper by {savings:,.2f} in total cost.",
            "monthly_difference": round(abs(a["monthly_payment"] - b["monthly_payment"]), 2),
            "summary": (
                f"Option A: {a['monthly_payment']:,.2f}/mo, {option_a_years}yr, total cost {a['total_cost']:,.2f} (APR {a['true_apr']}%). "
                f"Option B: {b['monthly_payment']:,.2f}/mo, {option_b_years}yr, total cost {b['total_cost']:,.2f} (APR {b['true_apr']}%). "
                f"Option {better} saves {savings:,.2f} overall."
            ),
        }

    @mcp.tool(tags={"loans", "credit"}, annotations={"readOnlyHint": True})
    def true_credit_cost(
        purchase_price: Annotated[float, Field(description="Original price of item or loan amount", gt=0)],
        monthly_payment: Annotated[float, Field(description="Monthly payment amount", gt=0)],
        num_payments: Annotated[int, Field(description="Total number of payments (months)", ge=1)],
        upfront_fees: Annotated[float, Field(description="Any upfront fees, activation costs, or down payment required", ge=0)] = 0,
        annual_late_fee: Annotated[float, Field(description="Expected annual late fees (0 if always on time)", ge=0)] = 0,
    ) -> dict:
        """Find the true total cost and implied APR of any credit product.

        Works for car financing, buy-now-pay-later, credit card minimum payments,
        personal loans, and any fixed payment schedule. Cuts through misleading
        '0% financing' or low-rate marketing to show actual cost.
        """
        total_paid = monthly_payment * num_payments + upfront_fees + annual_late_fee * (num_payments / 12)
        total_interest = total_paid - purchase_price
        interest_rate_over_term = total_interest / purchase_price * 100

        # Calculate implied monthly rate via Newton's method
        if total_interest <= 0:
            implied_apr = 0.0
        else:
            r = 0.01  # initial guess
            for _ in range(200):
                fv = purchase_price * (1 + r) ** num_payments - monthly_payment * ((1 + r) ** num_payments - 1) / r
                dfv = (purchase_price * num_payments * (1 + r) ** (num_payments - 1)
                       - monthly_payment * (num_payments * (1 + r) ** (num_payments - 1) * r - ((1 + r) ** num_payments - 1)) / r ** 2)
                if abs(dfv) < 1e-10:
                    break
                r = r - fv / dfv
                r = max(r, 0.0001)
            implied_apr = r * 12 * 100

        cost_per_dollar = total_paid / purchase_price

        return {
            "purchase_price": purchase_price,
            "monthly_payment": monthly_payment,
            "number_of_payments": num_payments,
            "upfront_fees": upfront_fees,
            "total_paid": round(total_paid, 2),
            "total_interest_and_fees": round(total_interest, 2),
            "interest_as_pct_of_price": f"{interest_rate_over_term:.1f}%",
            "implied_apr": f"{implied_apr:.2f}%",
            "cost_per_dollar_borrowed": round(cost_per_dollar, 4),
            "verdict": (
                "Excellent — very low financing cost" if implied_apr < 3 else
                "Good — below typical personal loan rates" if implied_apr < 8 else
                "Acceptable — similar to standard bank rates" if implied_apr < 15 else
                "High — above average, explore alternatives" if implied_apr < 25 else
                "Very high — credit card territory, pay off ASAP"
            ),
            "summary": (
                f"You pay {total_paid:,.2f} for something that costs {purchase_price:,.2f}. "
                f"That's {total_interest:,.2f} in interest/fees ({interest_rate_over_term:.1f}% of price), "
                f"implying an APR of {implied_apr:.2f}%."
            ),
        }

    @mcp.tool(tags={"loans", "debt"}, annotations={"readOnlyHint": True})
    def debt_payoff_plan(
        balance: Annotated[float, Field(description="Current debt balance", gt=0)],
        annual_rate_pct: Annotated[float, Field(description="Annual interest rate % of the debt", ge=0)],
        monthly_payment: Annotated[float, Field(description="Current or planned monthly payment", gt=0)],
        extra_monthly: Annotated[float, Field(description="Extra amount you could add to the monthly payment (0 for base plan)", ge=0)] = 0,
    ) -> dict:
        """Calculate how long to pay off a debt and how much interest you'll pay.

        Compares the base payment plan vs adding extra monthly payments,
        showing exactly how many months and dollars you save.
        """
        def payoff(balance, monthly_rate, payment):
            if payment <= balance * monthly_rate and monthly_rate > 0:
                return None, None  # payment too low, never pays off
            months = 0
            total_interest = 0
            b = balance
            while b > 0 and months < 1200:
                interest = b * monthly_rate
                principal = min(payment - interest, b)
                total_interest += interest
                b -= principal
                months += 1
            return months, total_interest

        monthly_rate = annual_rate_pct / 100 / 12
        base_months, base_interest = payoff(balance, monthly_rate, monthly_payment)
        extra_months, extra_interest = payoff(balance, monthly_rate, monthly_payment + extra_monthly) if extra_monthly > 0 else (None, None)

        result = {
            "current_balance": balance,
            "annual_rate": f"{annual_rate_pct}%",
            "base_plan": {
                "monthly_payment": monthly_payment,
                "months_to_payoff": base_months,
                "years_to_payoff": round(base_months / 12, 1) if base_months else None,
                "total_interest": round(base_interest, 2) if base_interest is not None else None,
            },
        }

        if extra_monthly > 0 and extra_months is not None:
            months_saved = (base_months or 0) - extra_months
            interest_saved = (base_interest or 0) - extra_interest
            result["accelerated_plan"] = {
                "monthly_payment": monthly_payment + extra_monthly,
                "months_to_payoff": extra_months,
                "years_to_payoff": round(extra_months / 12, 1),
                "total_interest": round(extra_interest, 2),
                "months_saved": months_saved,
                "interest_saved": round(interest_saved, 2),
            }
            result["summary"] = (
                f"Base plan: paid off in {base_months} months paying {base_interest:,.2f} in interest. "
                f"Adding {extra_monthly:,.2f}/month: paid off in {extra_months} months, saving {months_saved} months and {interest_saved:,.2f} in interest."
            )
        else:
            result["summary"] = (
                f"At {monthly_payment:,.2f}/month, you'll pay off {balance:,.2f} in {base_months} months "
                f"({base_months / 12:.1f} years), paying {base_interest:,.2f} in interest."
                if base_months else "Payment is too low to cover interest — increase your payment."
            )

        return result
