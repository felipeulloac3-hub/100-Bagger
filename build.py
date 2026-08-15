#!/usr/bin/env python3
"""Generate CHECKLIST.md and checklist.html from checklist.json.

checklist.json is the single source of truth. Edit it, run this, commit both outputs.
"""
import json
import pathlib
import collections

ROOT = pathlib.Path(__file__).parent
DATA = json.loads((ROOT / "checklist.json").read_text())

WEIGHT_LABEL = {"gate": "GATE", "major": "MAJOR", "minor": "MINOR"}


def tally():
    per_stage, totals = [], collections.Counter()
    for st in DATA["stages"]:
        w = collections.Counter(i[4] for i in st["items"])
        machine = sum(1 for i in st["items"] if i[3] in ("M", "M+H"))
        per_stage.append((st, w, machine))
        totals.update(w)
        totals.update(i[5] for i in st["items"])
        totals["machine"] += machine
        totals["items"] += len(st["items"])
    return per_stage, totals


def strip_html(s):
    for a, b in (("<strong>", "**"), ("</strong>", "**"), ("<em>", "*"), ("</em>", "*")):
        s = s.replace(a, b)
    return s.replace("&amp;", "&")


def build_md(per_stage, totals):
    L = [
        f"# {DATA['title']}",
        "",
        "A checklist for identifying businesses that could compound 100x, assembled from",
        "the published record of investors who actually caught them and the literature",
        "written about the phenomenon. Every question carries its source.",
        "",
        f"**Version {DATA['version']}** — {totals['items']} questions across "
        f"{len(DATA['stages'])} stages.",
        "",
        "## Scope",
        "",
        DATA["route"],
        "",
        "## Legend",
        "",
        "| Tag | Meaning |",
        "|---|---|",
        "| **GATE** | A failure disqualifies. Do not proceed, do not average against other scores. |",
        "| **MAJOR** | Weighted heavily. Multiple failures should stop you. |",
        "| **MINOR** | Informative. Rarely decisive alone. |",
        "| `M` | Machine-answerable from structured data or filings text |",
        "| `H` | Human judgment required |",
        "| `M+H` | Machine surfaces the evidence, human renders the verdict |",
        "| **book** | The source wrote this in a published book, letter or research paper |",
        "| **talk** | The source asked it in a recorded lecture or interview; phrasing approximate |",
        "| *derived* | The source described the principle; the question is my operationalization |",
        "",
        "## Provenance",
        "",
        DATA["provenance"],
        "",
        f"**{totals['book']} from published text, {totals['talk']} from recorded talks, "
        f"{totals['derived']} derived.**",
        "",
        "## Sources",
        "",
        "| Code | Source |",
        "|---|---|",
    ]
    for k, v in DATA["sources"].items():
        L.append(f"| {k} | {v} |")
    L += [
        "",
        "> **On Pabrai.** He has never published his list. What is documented is its",
        "> method, its category weighting (~150 questions; leverage, management and moat",
        "> at 70–80%), and questions he has named in talks. Items credited to him are",
        "> either publicly stated or direct operationalizations of a failure mode he has",
        "> described — not a leaked copy.",
        "",
        "---",
        "",
    ]

    for st, w, machine in per_stage:
        L += [f"## {st['n']} — {st['t']}", "", st["note"], ""]
        L += ["| # | Question | Source | Provenance | Type | Weight |", "|---|---|---|---|---|---|"]
        for id_, q, src, typ, wt, prov in st["items"]:
            pv = "*derived*" if prov == "derived" else f"**{prov}**"
            L.append(f"| {id_} | {strip_html(q)} | {src} | {pv} | `{typ}` | {WEIGHT_LABEL[wt]} |")
        if st.get("quote"):
            L += ["", f"> {strip_html(st['quote'])}"]
        L += ["", "---", ""]

    L += ["## Counts", "", "| Stage | Items | Gate | Major | Minor | Machine |", "|---|---|---|---|---|---|"]
    for st, w, machine in per_stage:
        L.append(
            f"| {st['n']} — {st['t']} | {len(st['items'])} | {w['gate'] or '—'} | "
            f"{w['major'] or '—'} | {w['minor'] or '—'} | {machine} |"
        )
    L.append(
        f"| **Total** | **{totals['items']}** | **{totals['gate']}** | "
        f"**{totals['major']}** | **{totals['minor']}** | **{totals['machine']}** |"
    )
    human_only = totals["items"] - totals["machine"]
    L += [
        "",
        f"{totals['machine']} questions are wholly or partly machine-answerable — the",
        f"automation target. The remaining {human_only} are yours, and no amount of",
        "engineering changes that.",
        "",
        "---",
        "",
        "## Not investment advice",
        "",
        "A research framework. A score is not a recommendation, and no checklist",
        "identifies a 100-bagger — 100x is a multi-decade outcome contingent on",
        "execution nobody can forecast. This concentrates attention on the few",
        "businesses showing the signature early.",
        "",
        "---",
        "",
        "*Generated from `checklist.json` by `build.py`. Edit the JSON, not this file.*",
        "",
    ]
    return "\n".join(L)


CSS = """
:root{
  --ground:#EDF0F3; --surface:#FBFCFD; --surface-2:#F4F6F8;
  --ink:#131A21; --ink-2:#3C4A55; --ink-3:#6B7B87;
  --rule:#D3DAE0; --rule-2:#E2E7EC;
  --accent:#1D4E6B; --accent-soft:#E4EDF2;
  --gate:#8A2E22; --gate-bg:#F6E7E4;
  --major:#7D5510; --major-bg:#F6EEDF;
  --minor:#4A5A66; --minor-bg:#EBEFF2;
  --machine:#1D4E6B; --human:#5B3A6B;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#0D1317; --surface:#151D23; --surface-2:#1B242B;
  --ink:#DDE5EB; --ink-2:#A7B6C1; --ink-3:#788895;
  --rule:#28343D; --rule-2:#1F2A32;
  --accent:#6DAECC; --accent-soft:#172B36;
  --gate:#E08A7B; --gate-bg:#33201C;
  --major:#D6A44A; --major-bg:#2E2617;
  --minor:#93A6B3; --minor-bg:#1E272E;
  --machine:#6DAECC; --human:#B18ECB;
}}
:root[data-theme="dark"]{
  --ground:#0D1317; --surface:#151D23; --surface-2:#1B242B;
  --ink:#DDE5EB; --ink-2:#A7B6C1; --ink-3:#788895;
  --rule:#28343D; --rule-2:#1F2A32;
  --accent:#6DAECC; --accent-soft:#172B36;
  --gate:#E08A7B; --gate-bg:#33201C;
  --major:#D6A44A; --major-bg:#2E2617;
  --minor:#93A6B3; --minor-bg:#1E272E;
  --machine:#6DAECC; --human:#B18ECB;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px}
h1,h2,h3{font-family:Georgia,"Iowan Old Style","Times New Roman",ui-serif,serif;
  font-weight:600;text-wrap:balance;margin:0}
header{border-bottom:1px solid var(--rule);background:var(--surface)}
.mast{padding:64px 0 44px;display:flex;flex-direction:column;gap:20px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:600}
h1{font-size:clamp(34px,6vw,54px);line-height:1.08;letter-spacing:-.015em}
.standfirst{font-size:18px;color:var(--ink-2);max-width:62ch;margin:0}
.routes{border:1px solid var(--rule);border-radius:3px;overflow:hidden;margin-top:8px;background:var(--surface-2)}
.routes-h{padding:14px 20px 10px;font-family:Georgia,ui-serif,serif;font-size:16px;font-weight:600;
  border-bottom:1px solid var(--rule)}
.route{display:grid;grid-template-columns:auto 1fr;gap:14px;padding:11px 20px;
  border-bottom:1px solid var(--rule-2);font-size:14px;color:var(--ink-2);align-items:baseline}
.route:last-child{border-bottom:none}
.route .rn{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--ink-3);white-space:nowrap}
.route.on{background:var(--accent-soft);color:var(--ink)}
.route.on .rn{color:var(--accent);font-weight:600}
.route b{font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--rule);
  border:1px solid var(--rule);border-radius:3px;overflow:hidden;margin-top:4px}
@media(min-width:720px){.tiles{grid-template-columns:repeat(4,1fr)}}
.tile{background:var(--surface-2);padding:16px 18px}
.tile .n{font-family:Georgia,ui-serif,serif;font-size:30px;line-height:1;font-variant-numeric:tabular-nums}
.tile .l{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);margin-top:7px}
.bar{position:sticky;top:0;z-index:20;background:var(--surface);border-bottom:1px solid var(--rule)}
.bar-in{display:flex;flex-wrap:wrap;gap:18px;padding:12px 0;align-items:center}
.grp{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.grp>.lab{font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;color:var(--ink-3);margin-right:2px}
button.f{font:inherit;font-size:12.5px;cursor:pointer;padding:4px 11px;border-radius:2px;
  border:1px solid var(--rule);background:transparent;color:var(--ink-2)}
button.f:hover{border-color:var(--accent);color:var(--accent)}
button.f[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--surface)}
button.f:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.count{margin-left:auto;font-size:12.5px;color:var(--ink-3);font-variant-numeric:tabular-nums}
main{padding-bottom:80px}
.stage{margin-top:52px}
.stage-h{display:flex;gap:16px;align-items:baseline;padding-bottom:12px;border-bottom:2px solid var(--ink)}
.stage-n{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--accent);font-weight:600;letter-spacing:.06em}
.stage-h h2{font-size:25px;letter-spacing:-.01em}
.stage-note{font-size:14.5px;color:var(--ink-2);margin:14px 0 4px;max-width:68ch}
blockquote{margin:20px 0 0;padding:14px 18px;border-left:2px solid var(--accent);
  background:var(--accent-soft);font-size:14px;color:var(--ink-2);border-radius:0 2px 2px 0}
blockquote em{color:var(--ink)}
.rows{margin-top:16px;border-top:1px solid var(--rule-2)}
.row{display:grid;grid-template-columns:auto 1fr;gap:2px 14px;padding:14px 16px 14px 14px;
  border-bottom:1px solid var(--rule-2);background:var(--surface);border-left:3px solid transparent}
.row.gate{border-left-color:var(--gate)}
.row.major{border-left-color:var(--major)}
.row.minor{border-left-color:var(--rule)}
.row .id{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--ink-3);
  font-variant-numeric:tabular-nums;padding-top:3px}
.q{font-size:15.5px;line-height:1.5}
.tags{grid-column:2;display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.tag{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;letter-spacing:.05em;
  padding:2px 7px;border-radius:2px;text-transform:uppercase;white-space:nowrap}
.t-gate{background:var(--gate-bg);color:var(--gate)}
.t-major{background:var(--major-bg);color:var(--major)}
.t-minor{background:var(--minor-bg);color:var(--minor)}
.t-src{background:transparent;color:var(--ink-3);border:1px solid var(--rule)}
.t-m{background:transparent;color:var(--machine);border:1px solid currentColor}
.t-h{background:transparent;color:var(--human);border:1px solid currentColor}
.t-book{background:var(--accent);color:var(--surface)}
.t-talk{background:var(--accent-soft);color:var(--accent);border:1px solid var(--accent)}
.t-derived{background:transparent;color:var(--ink-3);border:1px dashed var(--rule)}
.empty{padding:28px 14px;color:var(--ink-3);font-size:14px;background:var(--surface);
  border-bottom:1px solid var(--rule-2)}
.tbl-scroll{overflow-x:auto;margin-top:18px;border:1px solid var(--rule);border-radius:3px}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--surface);min-width:560px}
th,td{text-align:left;padding:9px 14px;border-bottom:1px solid var(--rule-2);vertical-align:top}
th{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);
  background:var(--surface-2);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:none}
td.k{font-weight:600;white-space:nowrap}
footer{border-top:1px solid var(--rule);background:var(--surface);padding:28px 0 44px;
  font-size:13px;color:var(--ink-3)}
footer p{max-width:68ch}
"""

ROUTES = [
    ("Route 1", "Commodity re-rating", "A supply-demand shift lifts a commodity price. Unforecastable; closer to a lottery than a process.", False),
    ("Route 2", "Capital-structure leverage", "Equity is a thin slice of enterprise value, so a doubling of the enterprise multiplies the equity many times over.", False),
    ("Route 3", "Inflation plus leverage", "The same mechanism, driven by a long inflationary expansion.", False),
    ("Route 4", "Reinvestment at high ROIC", "Earnings retained and redeployed above the cost of capital, compounding arithmetically over decades.", True),
]


def build_html(per_stage, totals):
    human_only = totals["items"] - totals["machine"]
    routes = "".join(
        f'<div class="route{" on" if on else ""}"><span class="rn">{n}</span>'
        f'<span><b>{t}</b> — {d}</span></div>'
        for n, t, d, on in ROUTES
    )
    return f"""<title>{DATA['title']}</title>
<style>{CSS}</style>
<header><div class="wrap mast">
<div class="eyebrow">Assembled from the published record</div>
<h1>{DATA['title']}</h1>
<p class="standfirst">{totals['items']} questions drawn from the investors who actually
caught hundred-baggers and the literature written about the phenomenon — Phelps, Mayer,
Davis, Lynch, Fisher, Akre, Russo, Sleep, Marathon, Mauboussin — each attributed, and each
marked for whether a machine or a human has to answer it.</p>
<div class="routes"><div class="routes-h">Phelps found four routes to 100x. This checklist screens for one.</div>{routes}</div>
<div class="tiles">
<div class="tile"><div class="n">{totals['items']}</div><div class="l">Questions</div></div>
<div class="tile"><div class="n">{totals['gate']}</div><div class="l">Disqualifying gates</div></div>
<div class="tile"><div class="n">{totals['machine']}</div><div class="l">Machine-answerable</div></div>
<div class="tile"><div class="n">{totals['book']}+{totals['talk']}</div><div class="l">The source's own words</div></div>
</div>
<p class="standfirst" style="font-size:15px">{DATA['provenance']}</p>
</div></header>

<div class="bar"><div class="wrap bar-in">
<div class="grp"><span class="lab">Weight</span>
<button class="f" data-w="gate" aria-pressed="false">Gate</button>
<button class="f" data-w="major" aria-pressed="false">Major</button>
<button class="f" data-w="minor" aria-pressed="false">Minor</button></div>
<div class="grp"><span class="lab">Answered by</span>
<button class="f" data-t="M" aria-pressed="false">Machine</button>
<button class="f" data-t="H" aria-pressed="false">Human</button></div>
<div class="grp"><span class="lab">Provenance</span>
<button class="f" data-p="book" aria-pressed="false">Book</button>
<button class="f" data-p="talk" aria-pressed="false">Talk</button>
<button class="f" data-p="derived" aria-pressed="false">Derived</button></div>
<div class="count" id="count"></div>
</div></div>

<main class="wrap" id="main"></main>

<footer><div class="wrap">
<p><strong>On Pabrai's list.</strong> He has never published it. What is documented is its
method, its category weighting, and questions he has named in talks. Items credited to him
here are publicly stated or direct operationalizations of a failure mode he has described —
not a leaked copy, and anything claiming to be one deserves suspicion.</p>
<p style="margin-top:14px"><strong>Not investment advice.</strong> A score is not a
recommendation. No checklist identifies a 100-bagger — 100x is a multi-decade outcome
contingent on execution nobody can forecast. This concentrates attention on the few
businesses showing the signature early.</p>
</div></footer>

<script>
const STAGES={json.dumps(DATA['stages'])};
const TOTAL={totals['items']};
const active={{w:new Set(),t:new Set(),p:new Set()}};
const main=document.getElementById('main'),countEl=document.getElementById('count');
main.innerHTML=STAGES.map(s=>{{
  const rows=s.items.map(([id,q,src,type,w,prov])=>`<div class="row ${{w}}" data-w="${{w}}" data-t="${{type}}" data-p="${{prov}}">
    <div class="id">${{id}}</div><div class="q">${{q}}</div>
    <div class="tags"><span class="tag t-${{w}}">${{w}}</span>
    <span class="tag ${{type==='H'?'t-h':'t-m'}}">${{type}}</span>
    <span class="tag t-src">${{src}}</span>
    <span class="tag t-${{prov}}">${{prov}}</span></div></div>`).join('');
  return `<section class="stage" data-stage>
    <div class="stage-h"><span class="stage-n">${{s.n}}</span><h2>${{s.t}}</h2></div>
    <p class="stage-note">${{s.note}}</p>
    <div class="rows">${{rows}}<div class="empty" hidden>No questions in this stage match the current filter.</div></div>
    ${{s.quote?`<blockquote>${{s.quote}}</blockquote>`:''}}</section>`;}}).join('');
function apply(){{
  let shown=0;
  document.querySelectorAll('[data-stage]').forEach(st=>{{
    let vis=0;
    st.querySelectorAll('.row').forEach(r=>{{
      const okW=!active.w.size||active.w.has(r.dataset.w);
      const okT=!active.t.size||[...active.t].some(f=>r.dataset.t.includes(f));
      const okP=!active.p.size||active.p.has(r.dataset.p);
      const ok=okW&&okT&&okP; r.hidden=!ok; if(ok){{vis++;shown++;}}
    }});
    st.querySelector('.empty').hidden=vis>0;
  }});
  countEl.textContent=`${{shown}} of ${{TOTAL}} shown`;
}}
document.querySelectorAll('button.f').forEach(b=>b.addEventListener('click',()=>{{
  const on=b.getAttribute('aria-pressed')==='true';
  b.setAttribute('aria-pressed',String(!on));
  const key=b.dataset.w?'w':(b.dataset.t?'t':'p');
  const val=b.dataset.w||b.dataset.t||b.dataset.p;
  on?active[key].delete(val):active[key].add(val);
  apply();
}}));
apply();
</script>
"""


def main():
    per_stage, totals = tally()
    (ROOT / "CHECKLIST.md").write_text(build_md(per_stage, totals))
    (ROOT / "checklist.html").write_text(build_html(per_stage, totals))
    print(f"{totals['items']} questions across {len(DATA['stages'])} stages")
    print(f"  gate {totals['gate']} / major {totals['major']} / minor {totals['minor']}")
    print(f"  machine {totals['machine']} / human-only {totals['items']-totals['machine']}")
    ids = [i[0] for st in DATA["stages"] for i in st["items"]]
    dupes = [k for k, v in collections.Counter(ids).items() if v > 1]
    assert not dupes, f"duplicate ids: {dupes}"
    print("  ids unique: ok")


if __name__ == "__main__":
    main()
