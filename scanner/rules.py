"""The Scan: the subset of checklist questions answerable from SEC XBRL alone.

Each rule maps to a checklist ID and returns PASS, FAIL or UNKNOWN with the
number behind it. UNKNOWN is a real outcome and never counts as a pass -- an
absent figure must not look like a clean bill of health.

Thresholds sourced to a named investor are marked SOURCED. The rest are my
judgment calls and are marked JUDGMENT, because a specific-looking number reads
as doctrine whether or not anyone ever endorsed it.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Callable

from . import metrics as M
from . import facts as F

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"

# JUDGMENT: how far back a late filing still counts against a company.
RECENT_LATE_FILING_YEARS = 2


def _years_before(date: str, years: int) -> str:
    d = _dt.date.fromisoformat(date)
    try:
        return d.replace(year=d.year - years).isoformat()
    except ValueError:                       # 29 February
        return d.replace(year=d.year - years, day=28).isoformat()


@dataclass
class Verdict:
    id: str
    status: str
    detail: str
    weight: str = "major"
    value: float | None = None

    @property
    def answered(self) -> bool:
        return self.status != UNKNOWN


@dataclass
class Context:
    """Everything a rule may read. Anything absent is simply None."""
    cik: str
    ticker: str
    name: str
    fx: dict                      # SEC companyfacts JSON
    forms: list[dict] = field(default_factory=list)   # submissions recent filings
    exchange: str | None = None
    price: float | None = None
    shares_out: float | None = None
    avg_dollar_volume: float | None = None
    # The date the scan is being run as of. The backtest sets this so recency
    # tests are measured from the historical date, not from today.
    as_of: str | None = None

    @property
    def as_of_date(self) -> str:
        return self.as_of or _dt.date.today().isoformat()

    @property
    def market_cap(self) -> float | None:
        if self.price is None or self.shares_out is None:
            return None
        return self.price * self.shares_out


RULES: list[tuple[str, str, Callable[[Context], Verdict]]] = []


def rule(cid: str, weight: str):
    def deco(fn):
        def wrapped(ctx: Context) -> Verdict:
            try:
                v = fn(ctx)
            except Exception as e:                      # a bad filing must not kill the scan
                return Verdict(cid, UNKNOWN, f"error: {type(e).__name__}: {e}", weight)
            v.id, v.weight = cid, weight
            return v
        RULES.append((cid, weight, wrapped))
        return wrapped
    return deco


def _v(status, detail, value=None):
    return Verdict("", status, detail, "", value)


def _cmp(value, threshold, direction, fmt, label, note):
    """PASS/FAIL against a threshold, or UNKNOWN when the value is missing."""
    if value is None:
        return _v(UNKNOWN, f"{label}: not derivable from filings")
    ok = value >= threshold if direction == "ge" else value <= threshold
    op = "≥" if direction == "ge" else "≤"
    return _v(PASS if ok else FAIL,
              f"{label} = {fmt.format(value)} (need {op} {fmt.format(threshold)}) — {note}",
              value)


# ── Stage 0: fatal flaws ──────────────────────────────────────────────────────

@rule("0.6", "gate")
def late_filings(ctx):
    """Late filings disqualify only when recent.

    A notice from five years ago is history; one from last year is a live signal
    about the finance function. Recency is the principled cut. The tempting
    alternative -- exempting the 2020-21 window when the SEC granted blanket
    COVID relief -- would be choosing dates to rescue a particular company, which
    is the curve-fitting this whole project exists to avoid.
    """
    if not ctx.forms:
        return _v(UNKNOWN, "no filing history available")
    nt = [f for f in ctx.forms if str(f.get("form", "")).startswith("NT ")]
    if not nt:
        return _v(PASS, "no NT 10-K or NT 10-Q on record")

    cutoff = _years_before(ctx.as_of_date, RECENT_LATE_FILING_YEARS)
    recent = [f for f in nt if f.get("filingDate", "") >= cutoff]
    listed = ", ".join(f"{f['form']} {f.get('filingDate', '')}" for f in nt[:4])

    if recent:
        return _v(FAIL, f"{len(recent)} late-filing notice(s) since {cutoff}: {listed} "
                        f"— JUDGMENT: {RECENT_LATE_FILING_YEARS}-year recency window")
    return _v(PASS, f"late filings exist but none since {cutoff} ({listed}) "
                    f"— JUDGMENT: treated as history, not a live signal")


@rule("0.11", "gate")
def major_exchange(ctx):
    if not ctx.exchange:
        return _v(UNKNOWN, "exchange not reported")
    ok = ctx.exchange.upper() in ("NYSE", "NASDAQ", "NYSEAMERICAN", "NYSE AMERICAN", "CBOE")
    return _v(PASS if ok else FAIL, f"listed on {ctx.exchange}")


@rule("0.12", "gate")
def real_business(ctx):
    rev = F.sum_keys(ctx.fx, ["revenue"])
    if rev is None:
        return _v(UNKNOWN, "no revenue reported in any 10-K")
    if rev <= 0:
        return _v(FAIL, "pre-revenue")
    dep = M.financing_dependence(ctx.fx)
    if dep is None:
        return _v(UNKNOWN, f"revenue {rev:,.0f} but cash flows incomplete")
    if dep > 0.5:
        return _v(FAIL, f"operations burn cash; financing covers {dep:.0%} of the gap "
                        "— funded by issuance, not by customers")
    return _v(PASS, f"revenue {rev:,.0f}; operations self-sustaining")


# ── Stage 2: engine one, earnings growth ──────────────────────────────────────

@rule("2.1", "major")
def roic_high_and_stable(ctx):
    s = [r for _, r in M.roic_series(ctx.fx, 5) if r is not None]
    if len(s) < 3:
        return _v(UNKNOWN, "fewer than 3 years of derivable ROIC")
    lo, avg = min(s), sum(s) / len(s)
    # JUDGMENT: Akre and Mayer both say "high and durable" without a number.
    ok = avg >= 0.15 and lo >= 0.10
    return _v(PASS if ok else FAIL,
              f"ROIC avg {avg:.1%}, min {lo:.1%} over {len(s)}y "
              f"(need avg ≥ 15% and min ≥ 10%) — JUDGMENT threshold", avg)


@rule("2.3", "major")
def incremental_returns(ctx):
    r = M.roiic(ctx.fx)
    if r is None:
        return _v(UNKNOWN, "ROIIC not derivable (capital did not grow, or gaps in data)")
    # JUDGMENT: Akre names the concept, not a threshold.
    return _v(PASS if r >= 0.15 else FAIL,
              f"return on incremental invested capital {r:.1%} (need ≥ 15%) — JUDGMENT", r)


@rule("2.5", "major")
def growth_band(ctx):
    g = M.revenue_cagr(ctx.fx, 3)
    if g is None:
        return _v(UNKNOWN, "3-year revenue CAGR not derivable")
    # SOURCED: Mayer's 20-25% sweet spot; >30% brings problems. Widened at the
    # bottom to 15% so the scan ranks rather than guillotines.
    if 0.15 <= g <= 0.35:
        note = "in Mayer's band" if 0.20 <= g <= 0.25 else "near Mayer's band"
        return _v(PASS, f"revenue CAGR {g:.1%} — {note} (SOURCED: Mayer)", g)
    return _v(FAIL, f"revenue CAGR {g:.1%} — outside 15–35% (SOURCED: Mayer's 20–25%)", g)


@rule("2.10", "major")
def cash_conversion(ctx):
    c = M.cash_conversion(ctx.fx)
    # SOURCED: Terry Smith treats cash conversion near 100% as a quality marker.
    return _cmp(c, 0.80, "ge", "{:.0%}", "FCF ÷ net income (3y)", "SOURCED: Smith")


@rule("2.11", "major")
def gross_margin(ctx):
    g = M.gross_margin(ctx.fx)
    # JUDGMENT: Fisher asks for a "worthwhile" margin and gives no number.
    return _cmp(g, 0.35, "ge", "{:.0%}", "gross margin", "JUDGMENT threshold")


@rule("2.13", "major")
def organic_growth(ctx):
    g = M.goodwill_share(ctx.fx)
    if g is None:
        return _v(UNKNOWN, "goodwill or total assets missing")
    # JUDGMENT: a proxy for roll-up dependence, not a sourced rule.
    return _v(PASS if g <= 0.30 else FAIL,
              f"goodwill + intangibles = {g:.0%} of assets (need ≤ 30%) — "
              "JUDGMENT proxy for acquisitive growth", g)


@rule("2.16", "major")
def not_cyclical_peak(ctx):
    d = M.revenue_drawdown(ctx.fx, 10)
    if d is None:
        return _v(UNKNOWN, "insufficient revenue history to test cyclicality")
    # JUDGMENT: a compounder's revenue rarely falls 25% in a year.
    return _v(PASS if d <= 0.25 else FAIL,
              f"worst peak-to-trough revenue decline {d:.0%} over available history "
              f"(need ≤ 25%) — JUDGMENT; large declines suggest Lynch's cyclical, "
              "not a fast grower", d)


@rule("2.17", "major")
def per_share_growth(ctx):
    e = M.eps_cagr(ctx.fx, 3)
    if e is None:
        return _v(UNKNOWN, "EPS CAGR not derivable")
    # JUDGMENT: Thorndike's per-share principle; the number is mine.
    return _v(PASS if e >= 0.12 else FAIL,
              f"diluted EPS CAGR {e:.1%} (need ≥ 12%) — growth that survives "
              "dilution — JUDGMENT threshold", e)


@rule("2.18", "minor")
def operating_leverage(ctx):
    o = M.operating_leverage(ctx.fx)
    return _cmp(o, 1.0, "ge", "{:.2f}x", "operating income growth ÷ revenue growth",
                "JUDGMENT threshold")


# ── Stage 3: engine two, the multiple ─────────────────────────────────────────

@rule("3.2", "major")
def peg(ctx):
    mc = ctx.market_cap
    ni = F.sum_keys(ctx.fx, ["net_income"])
    g = M.eps_cagr(ctx.fx, 3)
    if mc is None or ni is None or ni <= 0 or g is None or g <= 0:
        return _v(UNKNOWN, "PEG needs price, positive earnings and positive EPS growth")
    peg_v = (mc / ni) / (g * 100)
    # SOURCED: Mayer -- PEG not much above 1, on EARNINGS growth.
    return _v(PASS if peg_v <= 1.5 else FAIL,
              f"PEG {peg_v:.2f} (P/E {mc/ni:.1f} ÷ EPS growth {g:.0%}); need ≤ 1.5 "
              "— SOURCED: Mayer's 'not much above 1'", peg_v)


@rule("3.7", "major")
def return_without_rerating(ctx):
    """If the multiple never expands, does earnings growth alone still pay?"""
    g = M.eps_cagr(ctx.fx, 3)
    if g is None:
        return _v(UNKNOWN, "EPS growth not derivable")
    # JUDGMENT: 12% is roughly a long-run equity return plus a small premium.
    return _v(PASS if g >= 0.12 else FAIL,
              f"EPS growth alone delivers {g:.1%}/yr with no multiple expansion "
              "(need ≥ 12%) — JUDGMENT threshold", g)


# ── Stage 5: leverage and dilution ────────────────────────────────────────────

@rule("5.1", "major")
def leverage(ctx):
    nd = M.net_debt(ctx.fx)
    if nd is not None and nd <= 0:
        return _v(PASS, f"net cash position of {-nd:,.0f} — JUDGMENT: net cash passes "
                        "the leverage test outright", 0.0)
    r = M.debt_to_ebitda(ctx.fx)
    # JUDGMENT: Pabrai stresses leverage constantly but publishes no ratio.
    return _cmp(r, 1.5, "le", "{:.2f}x", "net debt ÷ EBITDA", "JUDGMENT threshold")


@rule("5.4", "major")
def near_term_maturities(ctx):
    due = F.sum_keys(ctx.fx, ["debt_due_1y", "debt_due_2y", "debt_due_3y"])
    if due is None:
        d = M.total_debt(ctx.fx)
        if d == 0 and M.has_balance_sheet(ctx.fx):
            return _v(PASS, "no debt outstanding — JUDGMENT: nothing to refinance",
                      0.0)
        return _v(UNKNOWN, "maturity schedule not tagged in XBRL")
    liquid = F.sum_keys(ctx.fx, ["cash", "short_term_investments"]) or 0.0
    f3 = M.fcf(ctx.fx) or 0.0
    covered = liquid + max(f3, 0) * 3
    return _v(PASS if due <= covered else FAIL,
              f"{due:,.0f} due within 3 years vs {covered:,.0f} of cash plus 3 years "
              "of current FCF — JUDGMENT coverage test", due)


@rule("5.5", "major")
def stress_test(ctx):
    ie = F.sum_keys(ctx.fx, ["interest_expense"])
    if ie is None or ie <= 0:
        # No interest expense only means something if we can see the balance sheet.
        if not M.has_balance_sheet(ctx.fx):
            return _v(UNKNOWN, "no interest expense tagged, and no balance sheet to "
                               "confirm the company is unlevered")
        return _v(PASS, "no material interest burden to stress — JUDGMENT: absence of "
                        "interest expense on a tagged balance sheet is read as unlevered",
                  999.0)
    s = M.stressed_interest_coverage(ctx.fx, 0.30)
    # JUDGMENT: the 30% decline and the 3x floor are both mine, not sourced.
    return _cmp(s, 3.0, "ge", "{:.1f}x",
                "interest coverage after a 30% revenue decline",
                "JUDGMENT: both the 30% shock and the 3x floor are my choices")


@rule("5.10", "major")
def growth_self_funded(ctx):
    s = M.self_funded(ctx.fx)
    if s is None:
        return _v(UNKNOWN, "operating cash flow history incomplete")
    return _v(PASS if s else FAIL,
              "operating cash covers capex over 3 years — JUDGMENT: cumulative FCF "
              "above zero is my operationalization of Cassel's self-funding test" if s
              else "capex exceeds operating cash over 3 years — growth needs outside "
                   "money, Cassel's principal micro-cap risk — JUDGMENT")


@rule("5.11", "major")
def dilution(ctx):
    d = M.dilution_rate(ctx.fx, 5)
    if d is None:
        return _v(UNKNOWN, "share count history not derivable")
    # JUDGMENT: 2%/yr allows genuine reinvestment without cancelling the holder's
    # share of it -- Fisher's Point 13 restated as a number he never gave.
    return _v(PASS if d <= 0.02 else FAIL,
              f"diluted share count {'+' if d >= 0 else ''}{d:.1%}/yr over 5 years "
              "(need ≤ +2%) — JUDGMENT threshold on Fisher #13", d)


@rule("5.12", "major")
def clean_capital_structure(ctx):
    pref = F.sum_keys(ctx.fx, ["preferred"])
    if pref is None:
        if not M.has_balance_sheet(ctx.fx):
            return _v(UNKNOWN, "no balance sheet tagged; cannot confirm capital structure")
        return _v(PASS, "no preferred stock reported — JUDGMENT: absence on a tagged "
                        "balance sheet is read as none outstanding", 0.0)
    if pref <= 0:
        return _v(PASS, "no preferred stock outstanding — JUDGMENT", 0.0)
    return _v(FAIL, f"preferred stock of {pref:,.0f} ranks ahead of common", pref)


# ── Stage 6: the jockey ───────────────────────────────────────────────────────

@rule("6.15", "major")
def stock_comp(ctx):
    s = M.sbc_share(ctx.fx)
    # JUDGMENT: Cassel warns about SBC without publishing a ratio.
    return _cmp(s, 0.10, "le", "{:.1%}", "stock-based comp ÷ revenue",
                "JUDGMENT threshold")


# ── Stage 7: earnings quality ─────────────────────────────────────────────────

@rule("7.1", "major")
def fcf_tracks_earnings(ctx):
    c = M.cash_conversion(ctx.fx, 5)
    return _cmp(c, 0.70, "ge", "{:.0%}", "FCF ÷ net income (5y)",
                "JUDGMENT threshold; persistent shortfall means reported profit "
                "is not turning into cash")


@rule("7.2", "major")
def receivables_quality(ctx):
    d = M.receivables_vs_revenue(ctx.fx)
    if d is None:
        return _v(UNKNOWN, "receivables or revenue history incomplete")
    # JUDGMENT: 5pp of drift is tolerable; more suggests the channel is being stuffed.
    return _v(PASS if d <= 0.05 else FAIL,
              f"receivables growing {d:+.1%}/yr faster than revenue (need ≤ +5pp) "
              "— JUDGMENT threshold", d)


@rule("7.8", "minor")
def goodwill_weight(ctx):
    g = M.goodwill_share(ctx.fx)
    return _cmp(g, 0.40, "le", "{:.0%}", "goodwill + intangibles ÷ assets",
                "JUDGMENT threshold")


# ── Stage 8: neglect and tradability ──────────────────────────────────────────

@rule("8.8", "major")
def tradable(ctx):
    if ctx.avg_dollar_volume is None:
        return _v(UNKNOWN, "no volume data")
    # JUDGMENT: enough to build a position over months without moving the price.
    return _v(PASS if ctx.avg_dollar_volume >= 50_000 else FAIL,
              f"median daily dollar volume {ctx.avg_dollar_volume:,.0f} "
              "(need ≥ 50,000) — JUDGMENT threshold", ctx.avg_dollar_volume)


# ── Scoring ───────────────────────────────────────────────────────────────────

WEIGHTS = {"gate": 0, "major": 3, "minor": 1}


@dataclass
class Result:
    ticker: str
    name: str
    cik: str
    verdicts: list[Verdict]
    market_cap: float | None = None

    @property
    def gate_failures(self) -> list[Verdict]:
        return [v for v in self.verdicts if v.weight == "gate" and v.status == FAIL]

    @property
    def excluded(self) -> bool:
        return bool(self.gate_failures)

    @property
    def answered(self) -> int:
        return sum(1 for v in self.verdicts if v.answered)

    @property
    def coverage(self) -> float:
        return self.answered / len(self.verdicts) if self.verdicts else 0.0

    @property
    def score(self) -> float | None:
        """Weighted share of ANSWERED non-gate questions that passed.

        Unanswered questions are excluded from both numerator and denominator,
        so the score never launders an UNKNOWN into a pass. Read it beside
        coverage or it will mislead.
        """
        num = den = 0
        for v in self.verdicts:
            w = WEIGHTS.get(v.weight, 0)
            if w == 0 or not v.answered:
                continue
            den += w
            if v.status == PASS:
                num += w
        return num / den if den else None

    @property
    def band(self) -> str:
        """Deliberately not a recommendation. It ranks reading priority only."""
        if self.excluded:
            return "excluded"
        if self.score is None or self.coverage < 0.5:
            return "insufficient data"
        if self.score >= 0.75:
            return "worth reading"
        if self.score >= 0.55:
            return "borderline"
        return "not yet"


def evaluate(ctx: Context) -> Result:
    return Result(ctx.ticker, ctx.name, ctx.cik,
                  [fn(ctx) for _, _, fn in RULES], ctx.market_cap)
