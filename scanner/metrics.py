"""Derived financial metrics.

Pure functions over normalized facts. Every function returns None rather than
guessing when the inputs are missing -- an absent metric must stay absent so the
rule layer can report UNKNOWN instead of silently passing.
"""
from __future__ import annotations

from . import facts as F

DEFAULT_TAX = 0.21  # US statutory; used only when the effective rate is unusable


def _d(a, b):
    """Divide, or None if that would be meaningless."""
    if a is None or b in (None, 0):
        return None
    return a / b


def effective_tax_rate(fx: dict, fy: int | None = None) -> float | None:
    tax = F.sum_keys(fx, ["tax"], fy)
    pre = F.sum_keys(fx, ["pretax_income"], fy)
    r = _d(tax, pre)
    return r if r is not None and 0.0 <= r <= 0.60 else None


def nopat(fx: dict, fy: int | None = None) -> float | None:
    ebit = F.sum_keys(fx, ["operating_income"], fy)
    if ebit is None:
        return None
    t = effective_tax_rate(fx, fy)
    return ebit * (1 - (t if t is not None else DEFAULT_TAX))


def total_debt(fx: dict, fy: int | None = None) -> float | None:
    return F.sum_keys(fx, ["debt_long", "debt_short"], fy)


def net_debt(fx: dict, fy: int | None = None) -> float | None:
    d = total_debt(fx, fy)
    if d is None:
        return None
    liquid = F.sum_keys(fx, ["cash", "short_term_investments"], fy) or 0.0
    return d - liquid


def invested_capital(fx: dict, fy: int | None = None) -> float | None:
    """Debt + equity - excess cash. The denominator of ROIC."""
    eq = F.sum_keys(fx, ["equity"], fy)
    if eq is None:
        return None
    debt = total_debt(fx, fy) or 0.0
    cash = F.sum_keys(fx, ["cash", "short_term_investments"], fy) or 0.0
    ic = eq + debt - cash
    return ic if ic > 0 else None


def roic(fx: dict, fy: int | None = None) -> float | None:
    return _d(nopat(fx, fy), invested_capital(fx, fy))


def roic_series(fx: dict, years: int = 5) -> list[tuple[int, float | None]]:
    rows = F.aligned(fx, ["operating_income", "equity", "debt_long", "debt_short",
                          "cash", "short_term_investments", "tax", "pretax_income"], years)
    return [(r["fy"], roic(fx, r["fy"])) for r in rows]


def roiic(fx: dict, years: int = 4) -> float | None:
    """Return on *incremental* invested capital: change in NOPAT over change in IC.

    Akre's third leg. Historical ROIC says the business is good; this says new
    money can still be put to work at that rate.
    """
    rows = F.aligned(fx, ["operating_income", "equity"], years + 1)
    if len(rows) < 2:
        return None
    first, last = rows[0]["fy"], rows[-1]["fy"]
    n0, n1 = nopat(fx, first), nopat(fx, last)
    ic0, ic1 = invested_capital(fx, first), invested_capital(fx, last)
    if None in (n0, n1, ic0, ic1):
        return None
    d_ic = ic1 - ic0
    if d_ic <= 0:
        return None  # capital shrank; ROIIC is not defined in a useful way
    return (n1 - n0) / d_ic


def fcf(fx: dict, fy: int | None = None) -> float | None:
    c = F.sum_keys(fx, ["cfo"], fy)
    if c is None:
        return None
    return c - (F.sum_keys(fx, ["capex"], fy) or 0.0)


def cash_conversion(fx: dict, years: int = 3) -> float | None:
    """Terry Smith's test: cumulative FCF over cumulative net income."""
    rows = F.aligned(fx, ["cfo", "capex", "net_income"], years)
    tot_fcf = tot_ni = 0.0
    n = 0
    for r in rows:
        if r["cfo"] is None or r["net_income"] is None:
            continue
        tot_fcf += r["cfo"] - (r["capex"] or 0.0)
        tot_ni += r["net_income"]
        n += 1
    if n < 2 or tot_ni <= 0:
        return None
    return tot_fcf / tot_ni


def gross_margin(fx: dict, fy: int | None = None) -> float | None:
    rev = F.sum_keys(fx, ["revenue"], fy)
    cogs = F.sum_keys(fx, ["cogs"], fy)
    if rev is None or cogs is None or rev <= 0:
        return None
    return (rev - cogs) / rev


MIN_SPAN = 2   # a growth rate needs at least this many years between endpoints


def revenue_cagr(fx: dict, years: int = 3) -> float | None:
    rows = [r for r in F.aligned(fx, ["revenue"], years + 1) if r["revenue"] is not None]
    if len(rows) < 2 or rows[-1]["fy"] - rows[0]["fy"] < MIN_SPAN:
        return None
    return F.cagr(rows[0]["revenue"], rows[-1]["revenue"], rows[-1]["fy"] - rows[0]["fy"])


def eps_cagr(fx: dict, years: int = 3) -> float | None:
    rows = F.aligned(fx, ["net_income", "shares_diluted"], years + 1)
    eps = [(r["fy"], r["net_income"] / r["shares_diluted"])
           for r in rows
           if r["net_income"] is not None and r["shares_diluted"] not in (None, 0)]
    if len(eps) < 2 or eps[-1][0] - eps[0][0] < MIN_SPAN:
        return None
    return F.cagr(eps[0][1], eps[-1][1], eps[-1][0] - eps[0][0])


def dilution_rate(fx: dict, years: int = 5) -> float | None:
    """Compound annual growth in diluted share count. Negative means buybacks."""
    rows = [r for r in F.aligned(fx, ["shares_diluted"], years + 1)
            if r["shares_diluted"] is not None]
    if len(rows) < 2 or rows[-1]["fy"] - rows[0]["fy"] < MIN_SPAN:
        return None
    return F.cagr(rows[0]["shares_diluted"], rows[-1]["shares_diluted"],
                  rows[-1]["fy"] - rows[0]["fy"])


def interest_coverage(fx: dict, fy: int | None = None) -> float | None:
    ie = F.sum_keys(fx, ["interest_expense"], fy)
    if ie is None or ie <= 0:
        return None  # no meaningful interest burden; the rule handles that case
    return _d(F.sum_keys(fx, ["operating_income"], fy), ie)


def stressed_interest_coverage(fx: dict, revenue_drop: float = 0.30) -> float | None:
    """Coverage after an immediate revenue decline, holding cost structure fixed
    below the gross line. Deliberately punitive: fixed costs do not fall.

    The 30% figure is a judgment call, not a sourced threshold.
    """
    ie = F.sum_keys(fx, ["interest_expense"])
    ebit = F.sum_keys(fx, ["operating_income"])
    rev = F.sum_keys(fx, ["revenue"])
    gm = gross_margin(fx)
    if None in (ie, ebit, rev, gm) or ie <= 0:
        return None
    lost_gross_profit = rev * revenue_drop * gm
    return (ebit - lost_gross_profit) / ie


def debt_to_ebitda(fx: dict) -> float | None:
    ebit = F.sum_keys(fx, ["operating_income"])
    da = F.sum_keys(fx, ["d_and_a"]) or 0.0
    if ebit is None:
        return None
    ebitda = ebit + da
    nd = net_debt(fx)
    if nd is None or ebitda <= 0:
        return None
    return nd / ebitda


def self_funded(fx: dict, years: int = 3) -> bool | None:
    """Does operating cash cover capex over a multi-year window? Cassel's test."""
    rows = F.aligned(fx, ["cfo", "capex"], years)
    tot = 0.0
    n = 0
    for r in rows:
        if r["cfo"] is None:
            continue
        tot += r["cfo"] - (r["capex"] or 0.0)
        n += 1
    return None if n < 2 else tot > 0


def financing_dependence(fx: dict, years: int = 3) -> float | None:
    """Financing inflows as a share of operating outflows.

    High and positive means the lights are kept on by issuing paper, which is
    Cassel's 'story, not a business'.
    """
    rows = F.aligned(fx, ["cfo", "cff"], years)
    cfo = sum(r["cfo"] for r in rows if r["cfo"] is not None)
    cff = sum(r["cff"] for r in rows if r["cff"] is not None)
    if not rows or cfo >= 0:
        return 0.0 if cfo >= 0 else None
    return _d(cff, abs(cfo))


def revenue_drawdown(fx: dict, years: int = 10) -> float | None:
    """Worst peak-to-trough annual revenue decline on record.

    A compounder's revenue rarely falls far. A cyclical's does, and that is the
    tell the checklist wants at 2.16.
    """
    rows = [r["revenue"] for r in F.aligned(fx, ["revenue"], years)
            if r["revenue"] is not None]
    if len(rows) < 3:
        return None
    peak, worst = rows[0], 0.0
    for v in rows[1:]:
        peak = max(peak, v)
        if peak > 0:
            worst = max(worst, (peak - v) / peak)
    return worst


def has_balance_sheet(fx: dict) -> bool:
    """Did this filer tag a balance sheet at all?

    Distinguishes "no preferred stock outstanding" from "this filer tags almost
    nothing", which would otherwise read identically -- as a pass.
    """
    return F.sum_keys(fx, ["equity"]) is not None or F.sum_keys(fx, ["assets"]) is not None


def goodwill_share(fx: dict) -> float | None:
    a = F.sum_keys(fx, ["assets"])
    g = F.sum_keys(fx, ["goodwill", "intangibles"])
    if a is None or a <= 0:
        return None
    return (g or 0.0) / a


def receivables_vs_revenue(fx: dict, years: int = 3) -> float | None:
    """Receivables growth minus revenue growth. Positive means DSO is stretching."""
    rows = [r for r in F.aligned(fx, ["revenue", "receivables"], years + 1)
            if r["revenue"] and r["receivables"]]
    if len(rows) < 2:
        return None
    n = rows[-1]["fy"] - rows[0]["fy"]
    rc = F.cagr(rows[0]["revenue"], rows[-1]["revenue"], n)
    ar = F.cagr(rows[0]["receivables"], rows[-1]["receivables"], n)
    if rc is None or ar is None:
        return None
    return ar - rc


def sbc_share(fx: dict) -> float | None:
    return _d(F.sum_keys(fx, ["sbc"]), F.sum_keys(fx, ["revenue"]))


def operating_leverage(fx: dict, years: int = 3) -> float | None:
    """Operating income growth divided by revenue growth. Above 1 means scale
    is dropping through to profit."""
    rows = [r for r in F.aligned(fx, ["revenue", "operating_income"], years + 1)
            if r["revenue"] and r["operating_income"]]
    if len(rows) < 2:
        return None
    n = rows[-1]["fy"] - rows[0]["fy"]
    rc = F.cagr(rows[0]["revenue"], rows[-1]["revenue"], n)
    oc = F.cagr(rows[0]["operating_income"], rows[-1]["operating_income"], n)
    if rc is None or oc is None or rc <= 0:
        return None
    return oc / rc
