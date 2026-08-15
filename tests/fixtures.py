"""Build synthetic companyfacts JSON matching the real SEC shape.

Lets the metric and rule layers be tested without network access, and lets us
construct company archetypes -- the compounder, the cyclical, the diluter -- that
would be hard to find and slow to fetch live.
"""
from __future__ import annotations

DURATION = {
    "revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
    "cogs": "CostOfGoodsAndServicesSold",
    "net_income": "NetIncomeLoss",
    "operating_income": "OperatingIncomeLoss",
    "pretax_income": "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "tax": "IncomeTaxExpenseBenefit",
    "cfo": "NetCashProvidedByUsedInOperatingActivities",
    "cff": "NetCashProvidedByUsedInFinancingActivities",
    "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
    "d_and_a": "DepreciationDepletionAndAmortization",
    "sbc": "ShareBasedCompensation",
    "interest_expense": "InterestExpense",
    "shares_diluted": "WeightedAverageNumberOfDilutedSharesOutstanding",
}

INSTANT = {
    "assets": "Assets",
    "liabilities": "Liabilities",
    "equity": "StockholdersEquity",
    "cash": "CashAndCashEquivalentsAtCarryingValue",
    "debt_long": "LongTermDebtNoncurrent",
    "debt_short": "LongTermDebtCurrent",
    "goodwill": "Goodwill",
    "receivables": "AccountsReceivableNetCurrent",
    "preferred": "PreferredStockValue",
}


def build(years: dict[int, dict[str, float]], name="Test Co", cik="0000000001") -> dict:
    """years: {fiscal_year: {logical_key: value}} -> companyfacts JSON."""
    gaap: dict = {}

    def add(concept, unit, row):
        node = gaap.setdefault(concept, {"label": concept, "units": {}})
        node["units"].setdefault(unit, []).append(row)

    for fy, vals in sorted(years.items()):
        accn = f"0000000001-{fy % 100:02d}-000001"
        filed = f"{fy + 1}-03-01"
        for key, val in vals.items():
            if val is None:
                continue
            unit = "shares" if key.startswith("shares") else "USD"
            if key in DURATION:
                add(DURATION[key], unit, {
                    "start": f"{fy}-01-01", "end": f"{fy}-12-31", "val": val,
                    "accn": accn, "fy": fy, "fp": "FY", "form": "10-K", "filed": filed,
                })
            elif key in INSTANT:
                add(INSTANT[key], unit, {
                    "end": f"{fy}-12-31", "val": val,
                    "accn": accn, "fy": fy, "fp": "FY", "form": "10-K", "filed": filed,
                })
            else:
                raise KeyError(f"unmapped fixture key: {key}")

    return {"cik": cik, "entityName": name, "facts": {"us-gaap": gaap}}


def compounder(start_fy=2020, n=6, growth=0.22) -> dict:
    """High ROIC, self-funded, minimal dilution, cash converting. Passes broadly."""
    years, rev, shares = {}, 100_000_000.0, 20_000_000.0
    equity, cash = 90_000_000.0, 40_000_000.0
    for i in range(n):
        fy = start_fy + i
        op = rev * 0.20
        ni = op * 0.79
        years[fy] = {
            "revenue": rev, "cogs": rev * 0.55, "operating_income": op,
            "pretax_income": op, "tax": op * 0.21, "net_income": ni,
            "cfo": ni * 1.15, "capex": rev * 0.04, "cff": -2_000_000.0,
            "d_and_a": rev * 0.03, "sbc": rev * 0.02, "interest_expense": 0.0,
            "shares_diluted": shares,
            "assets": equity * 1.4, "liabilities": equity * 0.4, "equity": equity,
            "cash": cash, "debt_long": 0.0, "debt_short": 0.0,
            "goodwill": equity * 0.10, "receivables": rev * 0.15, "preferred": 0.0,
        }
        rev *= 1 + growth
        equity += ni * 0.9
        cash += ni * 0.2
        shares *= 1.004          # ~0.4%/yr, well inside the 2% tolerance
    return build(years, "Compounder Inc")


def cyclical(start_fy=2020, n=6) -> dict:
    """Same average growth, but revenue collapses mid-history. Must fail 2.16."""
    path = [100, 145, 210, 120, 175, 250]      # a 43% peak-to-trough decline
    years, shares = {}, 20_000_000.0
    for i in range(n):
        fy = start_fy + i
        rev = path[i] * 1_000_000.0
        op = rev * 0.18
        ni = op * 0.79
        years[fy] = {
            "revenue": rev, "cogs": rev * 0.6, "operating_income": op,
            "pretax_income": op, "tax": op * 0.21, "net_income": ni,
            "cfo": ni * 1.1, "capex": rev * 0.05, "cff": 0.0,
            "d_and_a": rev * 0.04, "sbc": rev * 0.01, "interest_expense": 0.0,
            "shares_diluted": shares,
            "assets": 200_000_000.0, "liabilities": 60_000_000.0, "equity": 140_000_000.0,
            "cash": 30_000_000.0, "debt_long": 0.0, "debt_short": 0.0,
            "goodwill": 10_000_000.0, "receivables": rev * 0.15, "preferred": 0.0,
        }
    return build(years, "Cyclical Corp")


def diluter(start_fy=2020, n=6) -> dict:
    """Grows fast, funds it by issuing stock. Must fail 5.11 and 5.10."""
    years, rev, shares = {}, 50_000_000.0, 20_000_000.0
    for i in range(n):
        fy = start_fy + i
        op = rev * 0.05
        ni = op * 0.79
        years[fy] = {
            "revenue": rev, "cogs": rev * 0.7, "operating_income": op,
            "pretax_income": op, "tax": op * 0.21, "net_income": ni,
            "cfo": rev * 0.02, "capex": rev * 0.12, "cff": rev * 0.15,
            "d_and_a": rev * 0.05, "sbc": rev * 0.14, "interest_expense": 0.0,
            "shares_diluted": shares,
            "assets": 150_000_000.0, "liabilities": 40_000_000.0, "equity": 110_000_000.0,
            "cash": 25_000_000.0, "debt_long": 0.0, "debt_short": 0.0,
            "goodwill": 5_000_000.0, "receivables": rev * 0.2, "preferred": 0.0,
        }
        rev *= 1.30
        shares *= 1.18          # 18%/yr dilution
    return build(years, "Diluter Ltd")


def story(start_fy=2020, n=5) -> dict:
    """Burns cash, kept alive by financing. Must fail gate 0.12."""
    years, shares = {}, 30_000_000.0
    for i in range(n):
        fy = start_fy + i
        rev = 2_000_000.0 * (1.5 ** i)
        years[fy] = {
            "revenue": rev, "cogs": rev * 1.1, "operating_income": -20_000_000.0,
            "pretax_income": -20_000_000.0, "tax": 0.0, "net_income": -20_000_000.0,
            "cfo": -18_000_000.0, "capex": 3_000_000.0, "cff": 25_000_000.0,
            "d_and_a": 1_000_000.0, "sbc": 6_000_000.0, "interest_expense": 0.0,
            "shares_diluted": shares,
            "assets": 60_000_000.0, "liabilities": 15_000_000.0, "equity": 45_000_000.0,
            "cash": 30_000_000.0, "debt_long": 0.0, "debt_short": 0.0,
            "goodwill": 0.0, "receivables": rev * 0.3, "preferred": 0.0,
        }
        shares *= 1.25
    return build(years, "Story Co")


def sparse() -> dict:
    """A filer tagging almost nothing. Every rule must return UNKNOWN, never PASS."""
    return build({2023: {"revenue": 10_000_000.0}, 2024: {"revenue": 12_000_000.0}},
                 "Sparse Inc")
