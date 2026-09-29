"""Adapter: render a Letter / district view as self-contained HTML (printable) or plain text.
Used by the CLI and, unchanged, by the browser demo."""
from html import escape


def pct(x):
    return "—" if x is None else f"{100 * x:.1f}%"


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def headline(letter) -> str:
    if letter.peers < 2:
        return "No same-specialty peers this month: your own mix only, no comparison."
    if letter.above_median:
        return (f"Your Watch + Reserve share is above the median of {letter.peers} {letter.specialty} peers "
                f"({ordinal(letter.percentile)} percentile).")
    return (f"Your Watch + Reserve share is at or below the median of {letter.peers} {letter.specialty} peers. "
            f"Thank you for keeping first-choice Access antibiotics first.")


def letter_text(letter) -> str:
    out = [f"H1 MIRROR · {letter.month} · private to Reg. No. {letter.prescriber_reg} ({letter.specialty})",
           f"Your Watch + Reserve share: {pct(letter.wr_share)}  (Access {pct(letter.access_share)}, "
           f"{letter.lines} antibiotic lines)",
           f"Same-specialty peers ({letter.peers}): median {pct(letter.peer_median)} · you: "
           f"{ordinal(letter.percentile)} percentile",
           headline(letter)]
    if letter.not_recommended:
        out.append("WHO 'not recommended' combinations you prescribed: "
                   + "; ".join(f"{lb} ×{n}" for lb, n in letter.not_recommended))
    if letter.top_watch_reserve:
        out.append("Your most frequent Watch / Reserve lines: "
                   + "; ".join(f"{lb} ×{n}" for lb, n in letter.top_watch_reserve))
    out.append("A pattern, not a verdict: Watch drugs are right for some patients. No patient names are used.")
    return "\n".join(out)


def letter_html(letter) -> str:
    bar = max(0.0, min(1.0, letter.wr_share or 0))
    med = max(0.0, min(1.0, letter.peer_median or 0))
    tone = "#b45309" if letter.above_median else "#15803d"
    nr = "".join(f"<li>{escape(lb)} <b>×{n}</b></li>" for lb, n in letter.not_recommended) or "<li>None this month</li>"
    wr = "".join(f"<li>{escape(lb)} <b>×{n}</b></li>" for lb, n in letter.top_watch_reserve) or "<li>None</li>"
    return f"""<article class="h1m-letter" style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;
max-width:620px;border:1px solid #d1d5db;border-radius:14px;padding:22px 24px;background:#fff;color:#111827;line-height:1.45">
<div style="font-size:12px;letter-spacing:.06em;color:#047857;font-weight:700">H1 MIRROR · MONTHLY ANTIBIOTIC FEEDBACK · {escape(letter.month)}</div>
<div style="font-size:13px;color:#4b5563;margin-top:2px">Private to Reg. No. <b>{escape(letter.prescriber_reg)}</b> · {escape(letter.specialty)} · {letter.lines} antibiotic lines from local chemists</div>
<div style="font-size:26px;font-weight:800;color:{tone};margin:14px 0 2px">Your Watch + Reserve share: {pct(letter.wr_share)}</div>
<div style="font-size:14px;color:#374151">Same-specialty peers ({letter.peers}): median {pct(letter.peer_median)} · you: {ordinal(letter.percentile)} percentile</div>
<div aria-hidden="true" style="position:relative;height:14px;background:#ecfdf5;border-radius:7px;margin:12px 0 4px">
 <div style="position:absolute;left:0;top:0;bottom:0;width:{100 * bar:.1f}%;background:{tone};border-radius:7px;opacity:.85"></div>
 <div title="peer median" style="position:absolute;left:{100 * med:.1f}%;top:-4px;bottom:-4px;width:3px;background:#111827"></div>
</div>
<div style="font-size:11px;color:#6b7280">bar = your share · black tick = peer median</div>
<p style="font-size:15px;margin:12px 0">{escape(headline(letter))}</p>
<div style="display:flex;gap:18px;flex-wrap:wrap;font-size:13px">
 <div style="flex:1;min-width:220px"><b>WHO "not recommended" combinations you prescribed</b><ul style="margin:4px 0 0 18px;padding:0">{nr}</ul></div>
 <div style="flex:1;min-width:220px"><b>Your most frequent Watch / Reserve lines</b><ul style="margin:4px 0 0 18px;padding:0">{wr}</ul></div>
</div>
<p style="font-size:12px;color:#6b7280;margin:14px 0 0">A pattern, not a verdict: Watch antibiotics are right for some patients. Built from Schedule H1 register rows and bills your local chemists already keep; no patient names, no per-pharmacy report. Only you receive this letter. Classification: WHO AWaRe 2023 + WHO list of not-recommended combinations.</p>
</article>"""


def district_html(view) -> str:
    if view is None:
        return ("<p><b>District view withheld:</b> fewer than 10 pharmacies contributed this month "
                "(privacy threshold).</p>")
    return (f"<p><b>District aggregate</b> ({view['pharmacies']} pharmacies, {view['lines']} lines, no pharmacy or "
            f"prescriber names): Access {pct(view['access_share'])} · Watch + Reserve {pct(view['wr_share'])} · "
            f"WHO not-recommended combinations: {view['not_recommended_lines']} lines.</p>")
