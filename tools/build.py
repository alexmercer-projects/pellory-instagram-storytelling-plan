"""Build the static demo, its Letter print edition, and a PDF when Chrome is available."""
from html import escape
from pathlib import Path
import os
import shutil
from string import Template
import subprocess
import sys
import tempfile

from check_plan import FORMATS, WEEKDAYS, load_plan, report, stats, validate

ROOT = Path(__file__).resolve().parents[1]
PDF = "Pellory-Instagram-plan-DEMO.pdf"
NAV = (
    ("pillars", "Pillars"), ("calendar", "Calendar"), ("reels", "Reels"),
    ("carousels", "Carousels"), ("captions", "Captions"), ("stories", "Stories"),
    ("measuring", "Measuring"),
)
GOAL_NAMES = {"classes": "Classes", "drop": "Drop", "newsletter": "Newsletter", "awareness": "Awareness"}
FORMAT_ICONS = dict(zip(FORMATS, ("film", "stack", "image", "story")))
GLAZE_TONES = ("slate", "blue", "rust", "oat")

# The same hand-drawn silhouettes appear as test tiles, mock photos, and story art.
SYMBOLS = """<svg class="symbols" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" width="0" height="0">
<defs>
  <linearGradient id="shade-rust" x2=".86" y2="1"><stop stop-color="#efbd94"/><stop offset=".48" stop-color="#b76547"/><stop offset="1" stop-color="#6e382d"/></linearGradient>
  <linearGradient id="shade-blue" x2=".86" y2="1"><stop stop-color="#c9e1df"/><stop offset=".48" stop-color="#58859d"/><stop offset="1" stop-color="#314856"/></linearGradient>
  <linearGradient id="shade-oat" x2=".86" y2="1"><stop stop-color="#fff1d4"/><stop offset=".48" stop-color="#d8bb91"/><stop offset="1" stop-color="#705443"/></linearGradient>
  <linearGradient id="shade-moss" x2=".86" y2="1"><stop stop-color="#e2e4b6"/><stop offset=".48" stop-color="#919d66"/><stop offset="1" stop-color="#536043"/></linearGradient>
  <linearGradient id="shade-slate" x2=".86" y2="1"><stop stop-color="#d2d5c8"/><stop offset=".48" stop-color="#717e80"/><stop offset="1" stop-color="#394449"/></linearGradient>
  <pattern id="speckles" width="13" height="11" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="7" r=".65" fill="#372920"/><circle cx="10" cy="2" r=".5" fill="#f6dfc0"/>
    <circle cx="7" cy="9" r=".29" fill="#382218"/>
  </pattern>
  <symbol id="icon-wheel-mark" viewBox="0 0 32 32"><path d="M27 16a11 11 0 1 0-8 10.6m8-10.6a8 8 0 1 0-9 7.9m9-7.9a5 5 0 1 0-5.4 5m5.4-5a2 2 0 1 0-2 2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></symbol>
  <symbol id="icon-film" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 9h18M9 4l3 5m3-5 3 5m-8 4 5 2.5-5 2.5z"/></symbol>
  <symbol id="icon-stack" viewBox="0 0 24 24"><rect x="3" y="7" width="13" height="13" rx="2"/><path d="M8 4h10a3 3 0 0 1 3 3v8"/></symbol>
  <symbol id="icon-image" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 16 6-5 4 4 3-2 5 4"/><circle cx="16.5" cy="9" r="1"/></symbol>
  <symbol id="icon-story" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" stroke-dasharray="3 2"/><path d="M12 9v6m-3-3h6"/></symbol>
  <symbol id="icon-arrow" viewBox="0 0 24 24"><path d="M4 12h15m-6-6 6 6-6 6"/></symbol>
  <symbol id="icon-down" viewBox="0 0 24 24"><path d="M12 4v15m-6-6 6 6 6-6"/></symbol>
  <symbol id="art-cup" viewBox="0 0 200 160">
    <ellipse cx="101" cy="138" rx="66" ry="9" fill="#2f221b" opacity=".15"/>
    <path d="M132 57c47-14 50 35 5 50l-3-10c33-13 33-38 0-29Z" fill="var(--ceramic)" stroke="var(--shadow)" stroke-width="2"/>
    <path d="M48 48q47-14 88-1l-6 68q-4 17-39 18-34-2-38-18Z" fill="var(--ceramic)" stroke="var(--shadow)" stroke-width="2"/>
    <path d="M50 67q15 10 29 5t23 4q17 8 32-3l-3 41q-2 16-39 18-34-1-39-16Z" fill="var(--glaze)" opacity=".45"/>
    <path d="M49 52q43 9 86-2l-6 69q-10 13-40 13-30-3-34-15Z" fill="url(#speckles)" opacity=".52"/>
    <ellipse cx="92" cy="48" rx="44" ry="9" fill="var(--shadow)" stroke="var(--lit)" stroke-width="2"/>
    <path d="M59 116q32 13 66-1" fill="none" stroke="var(--lit)" stroke-opacity=".45"/>
  </symbol>
  <symbol id="art-bowl" viewBox="0 0 200 160">
    <ellipse cx="100" cy="133" rx="71" ry="8" fill="#2f221b" opacity=".17"/>
    <path d="M23 70q72-23 152 0-14 57-73 61Q40 132 23 70Z" fill="var(--ceramic)" stroke="var(--shadow)" stroke-width="2"/>
    <path d="M27 77q70 15 143 0-15 50-69 53Q45 129 27 77Z" fill="url(#speckles)" opacity=".52"/>
    <ellipse cx="99" cy="71" rx="76" ry="16" fill="var(--shadow)" stroke="var(--lit)" stroke-width="2.5"/>
    <path d="M30 73q70 23 138-1-13-10-64-11-46 0-74 12Z" fill="var(--glaze)" opacity=".5"/>
    <path d="M37 94q57 28 123 0" fill="none" stroke="var(--lit)" stroke-opacity=".5"/>
  </symbol>
  <symbol id="art-planter" viewBox="0 0 200 160">
    <path d="M103 64Q97 32 75 20m26 40q4-26 35-40m-32 36q-1-28 5-43" fill="none" stroke="var(--shadow)" stroke-width="3"/>
    <path d="M86 35Q58 31 62 12q18 1 24 23m26 0q15-22 32-24 2 19-32 24" fill="#718052"/>
    <path d="M55 59h90l-13 66q-29 15-64 1Z" fill="var(--ceramic)" stroke="var(--shadow)" stroke-width="2"/>
    <path d="m65 114 70 0-3 12q-31 14-64 0Z" fill="#ad6347"/>
    <ellipse cx="100" cy="60" rx="45" ry="10" fill="var(--shadow)" stroke="var(--lit)" stroke-width="2"/>
    <path d="M60 66q46 13 81 3l-8 45H66Z" fill="url(#speckles)"/>
  </symbol>
  <symbol id="art-wheel" viewBox="0 0 200 160">
    <ellipse cx="100" cy="93" rx="81" ry="54" fill="var(--ceramic)" stroke="var(--shadow)" stroke-width="2"/>
    <g fill="none" stroke="var(--lit)" stroke-width="1.9" opacity=".73">
      <ellipse cx="100" cy="93" rx="72" ry="46"/><ellipse cx="100" cy="92" rx="58" ry="36"/>
      <ellipse cx="100" cy="92" rx="44" ry="27"/><ellipse cx="100" cy="92" rx="30" ry="18"/>
    </g>
    <path d="M70 90q8-25 30-25t31 26q-17 24-61-1Z" fill="var(--glaze)" stroke="var(--shadow)" stroke-width="2"/>
    <path d="M122 85q-13-18-31-11" fill="none" stroke="var(--lit)" stroke-width="2"/>
  </symbol>
  <symbol id="art-map" viewBox="0 0 200 160">
    <path d="m29 29 118-16 24 110-117 20Z" fill="var(--lit)" stroke="var(--shadow)" stroke-width="2"/>
    <g fill="none" stroke="var(--shadow)" stroke-width="1.2" opacity=".65">
      <path d="M36 51q42-22 71-16t41-7M39 62q48-26 79-16 18 4 32-9M42 75q47-26 78-19 22 7 31-8M45 87q40-22 73-20 28 3 35-7M53 113q37-23 61-14 28 6 45-8M57 127q42-23 67-15 26 3 38-8"/>
    </g>
    <path d="M48 100q37-28 70-20 24 6 38-9" fill="none" stroke="#436c85" stroke-width="4"/>
    <path d="m132 138 43-79 6 3-43 80-8 6Z" fill="#a94b33" stroke="var(--shadow)"/>
  </symbol>
  <symbol id="art-kiln" viewBox="0 0 200 160">
    <path d="M38 135V69a62 62 0 0 1 124 0v66Z" fill="var(--glaze)" stroke="var(--shadow)" stroke-width="2"/>
    <path d="M53 134V71a47 47 0 0 1 94 0v63Z" fill="var(--shadow)" stroke="var(--lit)" stroke-width="2"/>
    <path d="M53 92h94m-94 22h94M38 80h15m94 0h15M38 110h15m94 0h15" fill="none" stroke="var(--lit)" stroke-width="2"/>
    <path d="M74 76h17l-2 15H76Zm35 0h17l-2 15h-13ZM67 103h30q-1 11-15 11t-15-11Zm38 0h30q-1 11-15 11t-15-11Z" fill="var(--lit)"/>
  </symbol>
  <symbol id="art-glaze" viewBox="0 0 200 160">
    <path d="m28 38 43-9 18 92-42 8Zm57-3 43 2-4 95-43-2Zm54 4 42 10-21 89-42-9Z" fill="var(--lit)" stroke="var(--shadow)" stroke-width="1.8"/>
    <path d="m27 37 44-9 9 45q-14-2-13 9l-2 17q-5 10-10-7t-19-17Z" fill="#49677a"/>
    <path d="m85 34 44 2-2 43q-13 1-14 15-2 12-8 5-6-11-7-17t-15-3Z" fill="#a9513a"/>
    <path d="m139 38 43 10-12 44q-17-4-20 6t-8 6l-2-18q-1-9-12-7Z" fill="#728254"/>
  </symbol>
  <symbol id="art-hands" viewBox="0 0 200 160">
    <ellipse cx="101" cy="111" rx="67" ry="27" fill="var(--glaze)" stroke="var(--shadow)" stroke-width="2"/>
    <ellipse cx="101" cy="109" rx="52" ry="17" fill="none" stroke="var(--lit)" opacity=".5"/>
    <path d="m26 33 17-11 26 31 26 14q14 9 3 15l-19-5 26 16q7 9-5 10l-16-7 4 7q-3 8-12 3L58 93q-13-8-17-21ZM176 28l-17-9-24 29-24 14q-10 9 1 13l14-3-21 14q-7 9 4 11l15-7-4 7q3 8 12 3l16-12q12-8 16-20Z" fill="var(--lit)" stroke="var(--shadow)" stroke-width="1.8"/>
  </symbol>
</defs></svg>"""


def svg(name, css="icon"):
    return f'<svg class="{css}" aria-hidden="true"><use href="#{escape(name)}"/></svg>'


def art(name, tone="rust"):
    return f'<div class="art tone-{escape(tone)}">{svg("art-" + name, "artwork")}</div>'


def paint(pillar):
    return f'style="--accent:{escape(pillar["color"])}"'


def title(label, heading, note=""):
    lead = f'<p class="section-note">{escape(note)}</p>' if note else ""
    return (f'<div class="section-head"><p class="eyebrow">{escape(label)}</p>'
            f'<h2>{escape(heading)}</h2>{lead}</div>')


def section(key, head, content, css=""):
    return f'<section class="section {css}" id="{key}"><div class="wrap">{head}{content}</div></section>'


def header(brand, has_pdf):
    links = "".join(f'<a href="#{key}">{label}</a>' for key, label in NAV)
    action = pdf_action("Get the PDF", "Print edition", has_pdf, "small outline header-pdf")
    return f"""<header class="site-header"><div class="wrap header-inner">
    <a class="wordmark" href="#main">{svg('icon-wheel-mark')} {escape(brand['name'])}</a>
    <nav aria-label="Plan sections">{links}</nav>
    {action}
    </div></header>"""


def pdf_action(download_label, print_label, available, css):
    if available:
        return f'<a class="button {css}" href="{PDF}" download>{download_label} {svg("icon-down")}</a>'
    return f'<a class="button {css}" href="plan-print.html">{print_label} {svg("icon-arrow")}</a>'


def hero(plan, printing, has_pdf):
    brand, intro = plan["brand"], plan["intro"]
    grid = "".join(art(name, tone) for name, tone in (
        ("cup", "blue"), ("wheel", "rust"), ("bowl", "oat"), ("map", "oat"), ("kiln", "slate"),
        ("planter", "moss"), ("bowl", "rust"), ("hands", "oat"), ("glaze", "blue"),
    ))
    actions = "" if printing else f"""<div class="hero-actions">
        <a class="button primary" href="#calendar">Explore the calendar {svg('icon-arrow')}</a>
        {pdf_action("Download the plan", "Open the print edition", has_pdf, "outline")}
      </div>"""
    visual = f"""<div class="hero-visual">
      <svg class="orbit" viewBox="0 0 510 530" aria-hidden="true"><g fill="none" stroke="currentColor">
        <ellipse cx="258" cy="268" rx="209" ry="223"/><ellipse cx="258" cy="268" rx="185" ry="197"/>
        <ellipse cx="258" cy="268" rx="163" ry="174"/><ellipse cx="258" cy="268" rx="143" ry="152"/>
        <path d="M258 21v33m0 428v28M20 268h31m416 0h26"/>
      </g></svg>
      <div class="phone profile">
        <div class="speaker"></div><div class="profile-inner">
          <div class="profile-top"><span>{escape(brand['handle'])}</span>{svg('icon-stack')}</div>
          <div class="profile-about">
            <div class="avatar">{svg('icon-wheel-mark')}</div>
            <div><strong>{escape(brand['name'])}</strong><span class="micro">Profile mockup</span></div>
          </div>
          <p>{escape(brand['profile_bio'])}</p>
          <div class="profile-grid" aria-hidden="true">{grid}</div>
        </div>
      </div>
      <span class="illustration-label">Illustrated profile</span>
    </div>"""
    first, second = map(escape, intro["headline"])
    return f"""<section class="hero wrap" aria-labelledby="hero-title"><div class="hero-copy">
      <p class="eyebrow">{escape(intro['eyebrow'])}</p>
      <h1 id="hero-title">{first}<br><em>{second}</em></h1>
      <p class="deck">{escape(intro['deck'])}</p>
      {actions}
      <div class="hero-meta"><span class="stamp">Concept demo <span>·</span> example data</span>
      <span class="micro">{escape(intro['period'])} <span>·</span> Alex Mercer</span></div>
    </div>{visual}</section>"""


def overview(plan, summary):
    chips = (
        (summary["days"], "Days planned"), (summary["formats"].get("Reel", 0), "Reels scheduled"),
        (summary["formats"].get("Carousel", 0), "Carousels scheduled"), (summary["tests"], "Tests to run"),
        (len(summary["captions"]), "Captions within limits"),
    )
    numbers = "".join(f"<li><strong>{number:02}</strong><span>{label}</span></li>" for number, label in chips)
    brand = plan["brand"]
    audience = "".join(f"<li><strong>{escape(item['name'])}</strong><p>{escape(item['description'])}</p></li>"
                       for item in brand["audiences"])
    glazes = "".join(f'<li class="tone-{tone}">{escape(name)}</li>'
                     for tone, name in zip(GLAZE_TONES, brand["glazes"]))
    return f"""<section class="overview"><div class="wrap">
      <h2 class="eyebrow">At a glance</h2><ul class="stat-list">{numbers}</ul>
      <div class="brand-note"><div><p class="eyebrow">{escape(brand['town'])} · Studio brief</p>
      <h3>{escape(brand['positioning'])}</h3><p>{escape(brand['origin'])}</p>
      <p>{escape(brand['profile_bio'])}</p>
      <p class="contact">{escape(brand['handle'])} · {escape(brand['email'])} · {escape(brand['phone'])}</p>
      <ul class="swatches" aria-label="Studio glaze names">{glazes}</ul></div>
      <div><h3 class="eyebrow">Who we're talking to</h3><ul class="audience-list">{audience}</ul></div></div>
    </div></section>"""


def pillars_voice(plan):
    cards = []
    for pillar, tone in zip(plan["pillars"], ("rust", "blue", "moss", "oat")):
        cards.append(f"""<article class="pillar-card" {paint(pillar)}>
          <div class="pillar-art">{art(pillar['art'], tone)}<span class="pillar-share">{pillar['share']}%</span></div>
          <div class="pillar-copy"><h3>{escape(pillar['name'])}</h3><p>{escape(pillar['purpose'])}</p>
          <div class="share-bar" style="--share:{pillar['share']}%" aria-hidden="true"></div>
          <p class="micro">{escape(' · '.join(pillar['formats']))}</p>
          <ul>{''.join(f'<li>{escape(idea)}</li>' for idea in pillar['ideas'])}</ul></div>
        </article>""")
    voice = plan["voice"]
    traits = "".join(f"""<article class="voice-trait"><h4>{escape(trait['name'])}</h4>
       <dl><div><dt>Sounds like</dt><dd>“{escape(trait['sounds_like'])}”</dd></div>
       <div><dt>Not like</dt><dd>“{escape(trait['not_like'])}”</dd></div></dl></article>"""
                     for trait in voice["traits"])
    rules = [
        ("Words we use", ", ".join(voice["words_use"])), ("Words we avoid", ", ".join(voice["words_avoid"])),
        ("Emoji", voice["emoji_rule"]), ("Caption formula", voice["caption_formula"]),
    ]
    rules_html = "".join(f'<div><dt>{label}</dt><dd>{escape(value)}</dd></div>' for label, value in rules)
    return section("pillars", title("Voice & pillars", "What to keep coming back to"),
                   f'<div class="pillar-grid">{"".join(cards)}</div><div class="voice"><h3>How June sounds</h3>'
                   f'<div class="voice-grid">{traits}</div><dl class="voice-rules">{rules_html}</dl></div>')


def calendar(plan, pillars, printing):
    options = (("pillar", "Pillar", [("all", "All pillars"), *[(k, p["name"]) for k, p in pillars.items()]]),
               ("format", "Format", [("all", "All formats"), *[(name, name) for name in FORMATS]]))
    groups = []
    for key, label, values in options:
        chips = "".join(f'<button type="button" data-value="{escape(value)}" aria-pressed="{str(value == "all").lower()}">'
                        f'{escape(name)}</button>' for value, name in values)
        groups.append(f'<div class="filter-group" role="group" aria-label="{label} filter" data-filter="{key}">{chips}</div>')
    filters = "" if printing else f'<div class="calendar-filters" hidden>{"".join(groups)}<p class="filter-count" role="status"></p></div>'
    legend = "".join(f'<li {paint(pillar)}><span></span>{escape(pillar["name"])}</li>' for pillar in pillars.values())
    weekdays = "".join(f"<span>{day}</span>" for day in WEEKDAYS)
    cells = []
    for row in sorted(plan["calendar"], key=lambda item: item["day"]):
        pillar = pillars[row["pillar"]]
        format_name = row["format"]
        linked = row.get("reel_id") or row.get("carousel_id")
        ref = ""
        if linked:
            kind = "Reel storyboard" if "reel_id" in row else "Carousel deck"
            ref = f'<a class="calendar-link" href="#{escape(linked)}">{kind} {svg("icon-arrow")}</a>'
        story = "" if format_name == "Stories only" else "<strong>Daily Story</strong> "
        css = " drop-day" if row["day"] == 26 else ""
        cells.append(f"""<li class="day{css}" {paint(pillar)} data-pillar="{escape(row['pillar'])}"
          data-format="{format_name}"><div class="day-top"><span>Day {row['day']:02} <small>{row['weekday']}</small></span>
          {svg('icon-' + FORMAT_ICONS[format_name])}</div>
          <p class="day-format">{format_name}</p><h3>{escape(row['title'])}</h3>
          <p class="day-story">{story}{escape(row['story'])}</p>{ref}
          <div class="day-bottom"><span>{escape(pillar['name'])}</span><span class="goal">{GOAL_NAMES[row['goal']]}</span></div></li>""")
    content = f"""{filters}<ul class="calendar-legend" aria-label="Pillar colors">{legend}</ul>
       <div class="weekdays" aria-hidden="true">{weekdays}</div><ol class="calendar-grid">{''.join(cells)}</ol>"""
    return section("calendar", title(plan["intro"]["period"], "The publishing calendar",
                                    plan["intro"]["calendar_note"]), content)


def reels(plan, pillars, printing):
    tabs = []
    cards = []
    for reel in plan["reels"]:
        key = escape(reel["id"])
        name = escape(reel["title"])
        tabs.append(f'<a id="tab-{key}" href="#{key}">{name}</a>')
        rows, slides, segments, stills = [], [], [], []
        for i, shot in enumerate(reel["shots"]):
            start, end = shot["start_s"], shot["end_s"]
            overlay = escape(shot["on_screen_text"])
            cells = (f"{start:02} to {end:02}s", escape(shot["description"]), overlay,
                     escape(shot["vo"]) or "Silent", escape(shot["edit_note"]))
            labels = ("Time", "Shot", "On-screen", "Voiceover", "Edit note")
            rows.append(f'<tr data-start="{start}" data-end="{end}">' + "".join(
                f'<td data-label="{label}">{value}</td>' for label, value in zip(labels, cells)) + "</tr>")
            illustration = art(shot["art"], "rust" if i % 2 == 0 else "blue")
            slides.append(f'<div class="shot-preview"{" hidden" if i else ""}>{illustration}'
                          f'<div class="safe"><span class="micro">Shot {i+1:02}</span><strong>{overlay}</strong></div></div>')
            stills.append(f'<li>{illustration}<span class="micro">Shot {i+1:02}</span></li>')
            segments.append(f'<button type="button" style="flex-grow:{end-start}" data-time="{start}" '
                            f'aria-label="Show shot {i+1}, {start} to {end} seconds">{i+1:02}</button>')
        controls = "" if printing else f"""<div class="shot-controls" hidden>
          <div class="segments" role="group" aria-label="Shot segments">{''.join(segments)}</div>
          <label class="sr-only" for="seek-{key}">Timeline for {name}</label>
          <input id="seek-{key}" class="scrub" type="range" min="0" max="{reel['length_s']}" value="0" step="1">
          <div class="transport"><button class="button outline small play" type="button">Play storyboard</button>
          <span class="reel-time micro">0s / {reel['length_s']}s</span></div></div>"""
        preview = f"""<div class="reel-display"><div class="phone reel-phone">{''.join(slides)}</div>
          <p class="micro illustration-note">Illustrated shot · dashed safe area</p>{controls}</div>"""
        if printing:
            preview = f'<ol class="print-stills" aria-label="Illustrated Reel shots">{"".join(stills)}</ol>'
        table = '<table class="shot-table"><thead><tr>' + "".join(f'<th scope="col">{label}</th>' for label in labels)
        table += f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        cards.append(f"""<article class="reel-panel" id="{key}" {paint(pillars[reel['pillar']])}>
          <div class="feature-head"><div><p class="eyebrow">{escape(pillars[reel['pillar']]['name'])} · {reel['length_s']} seconds</p>
          <h3>{name}</h3></div><a class="text-link" href="#{escape(reel['caption_id'])}">Read caption {svg('icon-arrow')}</a></div>
          <div class="reel-layout">{preview}<div class="reel-sheet">
            <div class="reel-brief"><p class="micro">First-second hook · {escape(reel['hook_type'])}</p>
            <p class="hook">“{escape(reel['hook'])}”</p><dl><div><dt>Audio</dt><dd>{escape(reel['audio'])}</dd></div>
            <div><dt>Cover</dt><dd>{escape(reel['cover_text'])}</dd></div></dl></div>{table}
          </div></div></article>""")
    tab_bar = "" if printing else f'<div class="reel-tabs" aria-label="Reel storyboards" hidden>{"".join(tabs)}</div>'
    return section("reels", title("Reel storyboards", "At the wheel, shot by shot",
                   "Six Reels with framing, audio and edit notes. Start with the hook on frame one."), tab_bar + "".join(cards),
                   "reels-section")


def carousels(plan, pillars, printing):
    cards = []
    mark = svg("icon-wheel-mark")
    for deck in plan["carousels"]:
        key, name = escape(deck["id"]), escape(deck["title"])
        slides, thumbs, dots = [], [], []
        for i, slide in enumerate(deck["slides"], 1):
            picture = art(slide["art"], slide["tone"])
            slide_title = escape(slide["title"])
            slides.append(f"""<li class="slide tone-{escape(slide['tone'])}"><div class="slide-kicker">
              {mark}<span>{i:02} / {len(deck['slides']):02}</span></div><h4>{slide_title}</h4>
              <p>{escape(slide['body'])}</p>{picture}</li>""")
            thumbs.append(f"""<li class="thumbnail"><div class="mini-slide tone-{escape(slide['tone'])}">{picture}
              <span>{i:02}</span></div><strong>{slide_title}</strong>
              <p>{escape(slide['visual'])}</p></li>""")
            dots.append(f'<button type="button" class="slide-dot" data-slide="{i-1}" aria-label="Slide {i}"></button>')
        arrows = "" if printing else f"""<div class="deck-controls" hidden>
          <button type="button" data-step="-1" aria-label="Previous slide">←</button>
          <div class="slide-dots" role="group" aria-label="Jump to a slide">{''.join(dots)}</div>
          <button type="button" data-step="1" aria-label="Next slide">→</button></div>"""
        cards.append(f"""<article class="carousel-deck" id="{key}">
          <div class="feature-head"><div><p class="eyebrow">{escape(pillars[deck['pillar']]['name'])} · {len(slides)} slides</p>
          <h3>{name}</h3></div><a class="text-link" href="#{escape(deck['caption_id'])}">Read caption {svg('icon-arrow')}</a></div>
          <div class="deck-frame"><div class="feed-top">{mark}<span>{escape(plan['brand']['handle'])}</span></div>
          <ol class="slides" aria-label="{name} slides"{'' if printing else ' tabindex="0"'}>{''.join(slides)}</ol>{arrows}</div>
          <ol class="thumbnails" aria-label="Slide art direction">{''.join(thumbs)}</ol></article>""")
    return section("carousels", title("Carousels", "A closer look, one slide at a time",
                   "Three illustrated decks with copy and art direction ready for design."), "".join(cards))


def captions(plan, summary, printing):
    by_id = {item["caption_id"]: item for item in (*plan["reels"], *plan["carousels"])}
    lengths = {item["id"]: item for item in summary["captions"]}
    cards = []
    for item in plan["captions"]:
        key = item["id"]
        source = by_id[key]
        count = lengths[key]
        first, body = count["first_line_chars"], count["body_chars"]
        paragraphs = "".join(f"<p>{escape(line)}</p>" for line in item["body"].split("\n\n"))
        detail = (f'<div class="full-caption">{paragraphs}</div>' if printing else
                  f'<details><summary>Read full caption</summary><div class="full-caption">{paragraphs}</div></details>')
        tags = " ".join(f'<span>{escape(tag)}</span>' for tag in item["hashtags"])
        cards.append(f"""<article class="caption-card" id="{escape(key)}">
          <p class="eyebrow">{'Reel' if 'shots' in source else 'Carousel'} caption</p>
          <h3>{escape(source['title'])}</h3><p class="first-line">{escape(item['first_line'])}</p>
          <div class="caption-meters"><label>First line <span>{first} / 125</span>
          <meter min="0" max="125" value="{first}">{first} of 125</meter></label>
          <label>Full caption <span>{body} / 2200</span>
          <meter min="0" max="2200" value="{body}">{body} of 2200</meter></label></div>
          {detail}<p class="hashtags">{tags}</p>
          <p class="alt-text"><strong>Alt text</strong> {escape(item['alt_text'])}</p></article>""")
    return section("captions", title("Caption library", "The line before “more”",
                   "Each caption includes its opening line, hashtags and alt text. The meters count the opening line and body separately."),
                   f'<div class="caption-grid">{"".join(cards)}</div>', "captions-section")


def stories(plan, printing):
    story = plan["stories"]
    cards = []
    for i, frame in enumerate(story["frames"], 1):
        sticker = escape(frame["type"].replace(" ", "-"))
        lines = "".join(f"<span>{escape(line)}</span>" for line in frame["sticker"])
        cards.append(f"""<li class="story-card"><div class="phone story-phone">
          {art(frame['art'], frame['tone'])}
          <div class="story-content"><span class="story-progress"></span><span class="micro">{escape(plan['brand']['handle'])}</span>
          <h3>{escape(frame['text'])}</h3><div class="sticker sticker-{sticker}">{lines}</div></div>
          </div><p class="micro">Day {frame['day']} · {i:02} · {escape(frame['type'])}</p></li>""")
    return section("stories", title("Story sequence", story["title"], story["period"]),
                   f'<ol class="story-strip" aria-label="Seven Story frames"{"" if printing else " tabindex=\"0\""}>{"".join(cards)}</ol>')


def measurement(plan):
    measure = plan["measurement"]
    rows = "".join(f"""<tr><th scope="row">{escape(goal['name'])}</th>
      <td data-label="What to track">{escape(goal['metrics'])}</td>
      <td data-label="Where to look">{escape(goal['source'])}</td></tr>""" for goal in measure["goals"])
    checklist = "".join(f"<li>{escape(text)}</li>" for text in measure["review"])
    tests = []
    for test in measure["tests"]:
        items = "".join(f"<div><dt>{label}</dt><dd>{escape(test[key])}</dd></div>" for key, label in (
            ("hypothesis", "Hypothesis"), ("how", "How to run"), ("compare", "What to compare"),
            ("decision", "Decision rule"),
        ))
        tests.append(f'<article class="test-card"><h4>{escape(test["name"])}</h4><dl>{items}</dl></article>')
    return section("measuring", title("Measuring it", "What I'd look at on Monday"),
                   f"""<aside class="honesty-box">{svg('icon-wheel-mark')}<p>{escape(measure['note'])}</p></aside>
                   <table class="metrics"><thead><tr><th scope="col">Goal</th><th scope="col">What to track</th>
                   <th scope="col">Where to look</th></tr></thead><tbody>{rows}</tbody></table>
                   <div class="weekly"><h3>Weekly review</h3><ul>{checklist}</ul></div>
                   <h3 class="test-heading">Three tests to run</h3><div class="test-grid">{''.join(tests)}</div>""")


def files(summary, printing, has_pdf):
    print_link = (f'<a class="text-link" href="plan-print.html">Open print edition {svg("icon-arrow")}</a>'
                  if has_pdf else "")
    actions = "" if printing else f"""<div class="file-actions">
      {pdf_action("Download the PDF", "Open the print edition", has_pdf, "primary")}
      <a class="button outline" href="data/plan.json" download>Download plan.json {svg('icon-down')}</a>
      {print_link}</div>"""
    return section("files", title("Files", "Take the plan with you"),
                   f'{actions}<h3 class="eyebrow">Plan validation report</h3><pre>{escape(report(summary))}</pre>')


def render(plan, summary, printing=False, has_pdf=False):
    brand = plan["brand"]
    pillars = {item["id"]: item for item in plan["pillars"]}
    template = Template((ROOT / "tools" / "template.html").read_text(encoding="utf-8"))
    content = (
        overview(plan, summary), pillars_voice(plan), calendar(plan, pillars, printing),
        reels(plan, pillars, printing), carousels(plan, pillars, printing), captions(plan, summary, printing),
        stories(plan, printing), measurement(plan), files(summary, printing, has_pdf),
    )
    return template.substitute(
        title=f"{escape(brand['name'])} · 30-day Instagram plan" + (" · Print edition" if printing else ""),
        description=escape(brand["positioning"]), script="" if printing else '<script src="app.js" defer></script>',
        **{"class": ' class="print-edition"' if printing else ""},
        symbols=SYMBOLS, header="" if printing else header(brand, has_pdf), hero=hero(plan, printing, has_pdf),
        content="\n".join(content),
        footer="""<footer class="site-footer"><div class="wrap">
        <p><strong>Concept demo by Alex Mercer</strong><br>Fictional studio. Example data. No results are claimed.</p>
        <p>Fraunces, DM Sans and DM Mono · SIL Open Font License 1.1</p></div></footer>""",
    )


def main():
    plan = load_plan()
    errors = validate(plan)
    if errors:
        sys.exit("Cannot build the plan:\n" + "\n".join(errors))
    summary = stats(plan)
    (ROOT / "plan-print.html").write_text(render(plan, summary, printing=True), encoding="utf-8")
    print("Wrote plan-print.html", flush=True)
    node = shutil.which("node")
    if node and shutil.which(os.environ.get("CHROME", "google-chrome")):
        result = subprocess.run(
            [node, str(ROOT / "tools" / "make_pdf.mjs"), str(ROOT / "plan-print.html"), str(ROOT / PDF)],
            capture_output=True, text=True, timeout=90,
        )
        if result.returncode == 0 and (ROOT / PDF).is_file():
            print(f"Wrote {PDF}")
        else:
            print(f"PDF export failed. The print HTML is ready.\n{result.stderr.strip()}", file=sys.stderr)
    else:
        print("node or google-chrome unavailable. Open plan-print.html to print or save as PDF.")
    page = render(plan, summary, has_pdf=(ROOT / PDF).is_file())
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print("Wrote index.html")


if __name__ == "__main__":
    main()
