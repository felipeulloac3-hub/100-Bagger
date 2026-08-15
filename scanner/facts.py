"""Normalize SEC XBRL companyfacts JSON into tidy, comparable series.

The messy part of SEC data is that the same economic quantity appears under
different concept tags depending on the filer and the year, and the same period
is reported by several filings. Everything here exists to flatten that.

No network access. Pure functions over already-fetched JSON, so this is the
layer that carries the tests.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

# Concept fallback chains, most-preferred first. A filer may use any of them.
CONCEPTS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ],
    "cogs": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "pretax_income": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"],
    "tax": ["IncomeTaxExpenseBenefit"],
    "cfo": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "cff": [
        "NetCashProvidedByUsedInFinancingActivities",
        "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "d_and_a": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "DepreciationAndAmortization",
    ],
    "sbc": ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"],
    "interest_expense": ["InterestExpense", "InterestExpenseDebt", "InterestExpenseNonoperating"],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "short_term_investments": ["ShortTermInvestments", "MarketableSecuritiesCurrent"],
    "debt_long": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "debt_short": ["LongTermDebtCurrent", "ShortTermBorrowings", "DebtCurrent"],
    "debt_due_1y": ["LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths"],
    "debt_due_2y": ["LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"],
    "debt_due_3y": ["LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree"],
    "goodwill": ["Goodwill"],
    "intangibles": ["FiniteLivedIntangibleAssetsNet", "IntangibleAssetsNetExcludingGoodwill"],
    "receivables": ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"],
    "inventory": ["InventoryNet"],
    "preferred": ["PreferredStockValue"],
    "shares_diluted": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "shares_basic": ["WeightedAverageNumberOfSharesOutstandingBasic",
                     "WeightedAverageNumberOfSharesOutstanding"],
}

# Concepts measured at an instant (balance sheet) rather than over a period.
INSTANT = {
    "assets", "liabilities", "equity", "cash", "short_term_investments",
    "debt_long", "debt_short", "debt_due_1y", "debt_due_2y", "debt_due_3y",
    "goodwill", "intangibles", "receivables", "inventory", "preferred",
}


# Quantities not denominated in dollars. Getting this wrong yields an empty
# series rather than an error, which is exactly the kind of silent hole that
# makes a screen quietly stop testing something.
UNIT_FOR = {"shares_diluted": "shares", "shares_basic": "shares"}


def unit_for(key: str, unit: str | None = None) -> str:
    return unit if unit is not None else UNIT_FOR.get(key, "USD")


@dataclass(frozen=True)
class Point:
    """One observation, carrying enough provenance to cite it."""
    fy: int
    end: str
    val: float
    concept: str
    form: str
    accn: str
    filed: str

    def cite(self) -> str:
        return f"{self.concept} FY{self.fy} ({self.end}) = {self.val:,.0f} [{self.form} {self.accn}]"


def _days(start: str, end: str) -> int:
    f = "%Y-%m-%d"
    return (_dt.datetime.strptime(end, f) - _dt.datetime.strptime(start, f)).days


def _entries(facts: dict, concept: str, unit: str) -> list[dict]:
    for ns in ("us-gaap", "ifrs-full", "dei"):
        node = facts.get("facts", {}).get(ns, {}).get(concept)
        if node:
            for u, rows in node.get("units", {}).items():
                if u == unit:
                    return rows
    return []


def prune(facts: dict, as_of: str) -> dict:
    """Drop every fact filed after `as_of` (YYYY-MM-DD).

    The whole backtest rests on this. Two distinct forms of look-ahead die here:

    - Restatements. `series` prefers the most recently filed figure for a fiscal
      year, which on live data is right and in a 2011 backtest would silently
      substitute a 2015 restatement nobody could have seen.
    - Filing lag. FY2010 results are not public until the 10-K lands in early
      2011. Filtering on the filing date rather than the period end is what stops
      the screen reading results before they were published.

    Returns a new dict; the input is untouched. Facts with no filing date are
    dropped rather than kept, because an undated fact cannot be proven to have
    existed yet.
    """
    out = {k: v for k, v in facts.items() if k != "facts"}
    ns_out: dict = {}
    for ns, concepts in facts.get("facts", {}).items():
        c_out: dict = {}
        for concept, node in (concepts or {}).items():
            if not isinstance(node, dict):
                continue
            u_out: dict = {}
            for unit, rows in node.get("units", {}).items():
                kept = [r for r in rows
                        if isinstance(r, dict) and r.get("filed") and r["filed"] <= as_of]
                if kept:
                    u_out[unit] = kept
            if u_out:
                c_out[concept] = {**node, "units": u_out}
        if c_out:
            ns_out[ns] = c_out
    out["facts"] = ns_out
    return out


def series(facts: dict, key: str, unit: str | None = None) -> list[Point]:
    """Annual series for a logical quantity, newest last, one point per fiscal year.

    Walks the concept fallback chain and merges: a filer that switched tags
    mid-history still yields one continuous series. Where several filings report
    the same fiscal year, the most recently filed wins.
    """
    unit = unit_for(key, unit)
    instant = key in INSTANT
    best: dict[int, Point] = {}

    for concept in CONCEPTS.get(key, [key]):
        for r in _entries(facts, concept, unit):
            if r.get("form") not in ("10-K", "10-K/A", "20-F"):
                continue
            if r.get("fp") != "FY" and not instant:
                continue
            fy, end, filed = r.get("fy"), r.get("end"), r.get("filed", "")
            if fy is None or end is None or r.get("val") is None:
                continue
            if not instant:
                start = r.get("start")
                # Annual flows only: reject quarters and cumulative stubs.
                if not start or not (300 <= _days(start, end) <= 400):
                    continue
            p = Point(int(fy), end, float(r["val"]), concept, r.get("form", ""),
                      r.get("accn", ""), filed)
            prior = best.get(p.fy)
            # Prefer the later-filed figure; on a tie prefer the earlier concept
            # in the fallback chain, which is already guaranteed by iteration order.
            if prior is None or p.filed > prior.filed:
                best[p.fy] = p

    return [best[fy] for fy in sorted(best)]


def latest(facts: dict, key: str, unit: str | None = None) -> Point | None:
    s = series(facts, key, unit)
    return s[-1] if s else None


def value(facts: dict, key: str, unit: str | None = None) -> float | None:
    p = latest(facts, key, unit)
    return p.val if p else None


def sum_keys(facts: dict, keys: list[str], fy: int | None = None) -> float | None:
    """Sum several quantities for one fiscal year. None if every part is missing.

    A missing part is treated as zero only when at least one part is present --
    a company with no short-term debt simply omits the tag.
    """
    total, seen = 0.0, False
    for k in keys:
        s = series(facts, k)
        if not s:
            continue
        p = next((x for x in reversed(s) if fy is None or x.fy == fy), None)
        if p:
            total += p.val
            seen = True
    return total if seen else None


def aligned(facts: dict, keys: list[str], years: int = 5) -> list[dict]:
    """Rows of {fy, <key>: value|None} for the most recent `years` fiscal years.

    Aligned on fiscal year so ratios never mix periods -- the quiet way these
    calculations go wrong.
    """
    by_key = {k: {p.fy: p for p in series(facts, k)} for k in keys}
    all_fy = sorted({fy for m in by_key.values() for fy in m})[-years:]
    rows = []
    for fy in all_fy:
        row: dict = {"fy": fy}
        for k in keys:
            p = by_key[k].get(fy)
            row[k] = p.val if p else None
        rows.append(row)
    return rows


def cagr(first: float, last: float, periods: int) -> float | None:
    """Compound annual growth. None when the sign makes the result meaningless."""
    if periods <= 0 or first is None or last is None or first <= 0 or last <= 0:
        return None
    return (last / first) ** (1.0 / periods) - 1.0
