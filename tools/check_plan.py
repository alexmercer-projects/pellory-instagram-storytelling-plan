"""Validate the Pellory plan and report counts and caption lengths."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

PLAN_PATH = Path(__file__).resolve().parents[1] / "data" / "plan.json"
FORMATS = ("Reel", "Carousel", "Single image", "Stories only")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
GOALS = ("classes", "drop", "newsletter", "awareness")
STICKERS = {"photo-style", "poll", "quiz", "question box", "countdown sticker", "link sticker", "slider"}
ART = ("cup", "bowl", "planter", "wheel", "map", "kiln", "glaze", "hands")
TONES = ("rust", "blue", "oat", "moss", "slate")
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@([\w.-]+)")
PHONE = re.compile(r"(?<!\w)(?:(?:\+?\d{1,3}[ .-]?)?(?:\(\d{3}\)[ .-]*|\d{3}[ .-]?))?\d{3}[ .-]?\d{4}(?!\w)")
DEMO_PHONE = re.compile(r"\(555\) 01[0-9]{2}")
DASH = re.compile(r"\u2014|(?<!\d)\u2013|\u2013(?!\d)")


def load_plan(path=PLAN_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def strings(value, path="plan"):
    """Yield all strings with paths so copy errors can be located."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield path, key
            yield from strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            yield from strings(item, f"{path}[{index}]")


def validate(plan):
    errors = []
    if not isinstance(plan, dict):
        return ["Plan must be a JSON object."]

    def objects(value, label, low, high):
        if not isinstance(value, list) or not low <= len(value) <= high:
            count = str(low) if low == high else f"{low} to {high}"
            errors.append(f"{label} must contain {count} entries.")
        if not isinstance(value, list):
            return []
        if any(not isinstance(item, dict) for item in value):
            errors.append(f"{label} entries must be objects.")
        return [item for item in value if isinstance(item, dict)]

    def index_items(items, label):
        index = {}
        for item in items:
            key = item.get("id")
            if not isinstance(key, str) or not ID.fullmatch(key):
                errors.append(f"{label} entries require a lowercase ID.")
            elif key in index:
                errors.append(f"{label} contains duplicate ID {key}.")
            else:
                index[key] = item
        return index

    def reference(key, index, label):
        if not isinstance(key, str) or key not in index:
            errors.append(f"{label} references unknown ID {key!r}.")
            return {}
        return index[key]

    def required_text(item, fields, label):
        for field in fields.split():
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} needs non-empty {field} text.")

    def section(name):
        value = plan.get(name)
        if not isinstance(value, dict):
            errors.append(f"{name} must be an object.")
            return {}
        return value

    def text_list(item, field, label, count=None):
        value = item.get(field)
        if (not isinstance(value, list) or not value or (count is not None and len(value) != count)
                or any(not isinstance(line, str) or not line.strip() for line in value)):
            size = f" with {count} lines" if count is not None else ""
            errors.append(f"{label} needs a non-empty {field} list{size}.")

    def illustration(item, label, uses_tone=False):
        if item.get("art") not in ART:
            errors.append(f"{label} needs a valid illustration name.")
        if uses_tone and item.get("tone") not in TONES:
            errors.append(f"{label} needs a valid illustration tone.")

    brand = section("brand")
    required_text(brand, "name handle founder town positioning origin profile_bio", "Brand")
    text_list(brand, "glazes", "Brand", 4)
    for audience in objects(brand.get("audiences"), "Brand audiences", 3, 3):
        required_text(audience, "name description", "Brand audience")
    intro = section("intro")
    required_text(intro, "eyebrow deck period calendar_note", "Introduction")
    text_list(intro, "headline", "Introduction", 2)
    voice = section("voice")
    required_text(voice, "emoji_rule caption_formula", "Voice")
    for trait in objects(voice.get("traits"), "Voice traits", 4, 4):
        required_text(trait, "name sounds_like not_like", "Voice trait")
    for field in ("words_use", "words_avoid"):
        text_list(voice, field, "Voice")

    pillars = index_items(objects(plan.get("pillars"), "Pillars", 4, 4), "Pillars")
    calendar = objects(plan.get("calendar"), "Calendar", 30, 30)
    reels = index_items(objects(plan.get("reels"), "Reels", 6, 6), "Reels")
    carousels = index_items(objects(plan.get("carousels"), "Carousels", 3, 3), "Carousels")
    captions = index_items(objects(plan.get("captions"), "Captions", 9, 9), "Captions")
    stories = section("stories")
    required_text(stories, "title period", "Story sequence")
    frames = objects(stories.get("frames"), "Story frames", 7, 7)

    shares = [pillar.get("share") for pillar in pillars.values()]
    if any(type(share) is not int or not 0 <= share <= 100 for share in shares) or sum(shares) != 100:
        errors.append("Pillar shares must be whole percentages that sum to 100.")
    for key, pillar in pillars.items():
        label = f"Pillar {key}"
        required_text(pillar, "name purpose", label)
        text_list(pillar, "formats", label)
        text_list(pillar, "ideas", label)
        illustration(pillar, label)
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(pillar.get("color"))):
            errors.append(f"Pillar {key} needs a six-digit hex color.")

    days = [row.get("day") for row in calendar]
    if any(type(day) is not int for day in days) or sorted(days) != list(range(1, 31)):
        errors.append("Calendar day numbers must be unique and cover 1 to 30.")
    for row in calendar:
        day = row.get("day")
        label = f"Calendar day {day}"
        if type(day) is int and 1 <= day <= 30 and row.get("weekday") != WEEKDAYS[(day - 1) % 7]:
            errors.append(f"{label} weekday must follow the Monday start.")
        required_text(row, "title story", label)
        reference(row.get("pillar"), pillars, f"{label} pillar")
        if row.get("format") not in FORMATS:
            errors.append(f"{label} has an invalid format.")
        if row.get("goal") not in GOALS:
            errors.append(f"{label} has an invalid goal.")
        for field, format_name, index in (("reel_id", "Reel", reels), ("carousel_id", "Carousel", carousels)):
            if field in row:
                linked = reference(row[field], index, f"{label} {field}")
                if row.get("format") != format_name or linked and linked.get("pillar") != row.get("pillar"):
                    errors.append(f"{label} {field} must match its format and pillar.")

    caption_links = Counter()
    for index, kind in ((reels, "Reel"), (carousels, "Carousel")):
        for key, item in index.items():
            label = f"{kind} {key}"
            required_text(item, "title", label)
            reference(item.get("pillar"), pillars, f"{label} pillar")
            cap_id = item.get("caption_id")
            if reference(cap_id, captions, f"{label} caption_id"):
                caption_links[cap_id] += 1
    for key in captions:
        if caption_links[key] != 1:
            errors.append(f"Caption {key} must be used by exactly one Reel or Carousel.")

    for key, reel in reels.items():
        label = f"Reel {key}"
        required_text(reel, "hook hook_type audio cover_text", label)
        length = reel.get("length_s")
        if type(length) is not int or not 15 <= length <= 45:
            errors.append(f"{label} length_s must be 15 to 45 seconds.")
        end = 0
        for i, shot in enumerate(objects(reel.get("shots"), f"{label} shots", 4, 8), 1):
            shot_label = f"{label} shot {i}"
            required_text(shot, "description on_screen_text edit_note", shot_label)
            illustration(shot, shot_label)
            if not isinstance(shot.get("vo"), str):
                errors.append(f"{shot_label} needs a vo string (can be empty).")
            start, stop = shot.get("start_s"), shot.get("end_s")
            if type(start) is not int or type(stop) is not int or start != end or stop <= start:
                errors.append(f"{shot_label} timings must be contiguous from 0 with positive durations.")
            end = stop
        if end != length:
            errors.append(f"{label} shots must end at length_s ({length}).")

    for key, carousel in carousels.items():
        for slide in objects(carousel.get("slides"), f"Carousel {key} slides", 5, 7):
            label = f"Carousel {key} slide"
            required_text(slide, "title body visual", label)
            illustration(slide, label, uses_tone=True)
    for key, caption in captions.items():
        label = f"Caption {key}"
        first, body = caption.get("first_line"), caption.get("body")
        if not isinstance(first, str) or not first.strip() or "\n" in first or len(first) > 125:
            errors.append(f"{label} first_line must be one non-empty line of at most 125 characters.")
        if not isinstance(body, str) or not body.strip() or len(body) > 2200:
            errors.append(f"{label} body must be non-empty and at most 2200 characters.")
        if isinstance(first, str) and isinstance(body, str) and body.split("\n", 1)[0] != first:
            errors.append(f"{label} first_line must be the start of its body.")
        tags = caption.get("hashtags")
        if not isinstance(tags, list) or not 3 <= len(tags) <= 5:
            errors.append(f"{label} must have 3 to 5 hashtags.")
        if isinstance(tags, list):
            if any(not isinstance(tag, str) or not re.fullmatch(r"#\w+", tag) or tag != tag.lower() for tag in tags):
                errors.append(f"{label} hashtags must be lowercase, start with # and contain no spaces.")
            tags = [tag.casefold() for tag in tags if isinstance(tag, str)]
            if len(set(tags)) != len(tags):
                errors.append(f"{label} contains duplicate hashtags.")
        alt = caption.get("alt_text")
        if not isinstance(alt, str) or not alt.strip() or len(alt) > 300:
            errors.append(f"{label} alt_text is required and must be at most 300 characters.")

    types = []
    for frame in frames:
        required_text(frame, "text", "Story frame")
        illustration(frame, "Story frame", uses_tone=True)
        kind = frame.get("type")
        day = frame.get("day")
        types.append(kind)
        if type(day) is not int or day not in days:
            errors.append(f"Story frame references unknown calendar day {day!r}.")
        sticker = frame.get("sticker")
        if not isinstance(sticker, list) or not sticker or any(not isinstance(line, str) or not line.strip() for line in sticker):
            errors.append("Story frame needs sticker content.")
    if any(not isinstance(kind, str) for kind in types) or set(types) != STICKERS:
        errors.append("Story sequence must use each of the seven frame types once.")

    measurement = section("measurement")
    required_text(measurement, "note", "Measurement")
    for goal in objects(measurement.get("goals"), "Measurement goals", 4, 4):
        required_text(goal, "name metrics source", "Measurement goal")
    for test in objects(measurement.get("tests"), "Measurement tests", 3, 3):
        required_text(test, "name hypothesis how compare decision", "Measurement test")
    review = measurement.get("review")
    if not isinstance(review, list) or not review or any(not isinstance(line, str) or not line.strip() for line in review):
        errors.append("Measurement requires a weekly review checklist.")

    for path, value in strings(plan):
        if DASH.search(value):
            errors.append(f"{path} contains an em dash or an en dash used as a dash.")
        if any(not DEMO_PHONE.fullmatch(phone.group()) for phone in PHONE.finditer(value)):
            errors.append(f"{path} phone number must use (555) 01xx.")
        if any(email.group(1).rstrip(".").lower() != "example.com" for email in EMAIL.finditer(value)):
            errors.append(f"{path} email address must end in @example.com.")

    if not DEMO_PHONE.fullmatch(str(brand.get("phone"))):
        errors.append("Brand phone number must use (555) 01xx.")
    email = EMAIL.fullmatch(str(brand.get("email")))
    if not email or email.group(1).lower() != "example.com":
        errors.append("Brand email address must end in @example.com.")
    return errors


def stats(plan):
    return {
        "days": len(plan["calendar"]),
        "formats": dict(Counter(row["format"] for row in plan["calendar"])),
        "reels": len(plan["reels"]),
        "carousels": len(plan["carousels"]),
        "story_frames": len(plan["stories"]["frames"]),
        "tests": len(plan["measurement"]["tests"]),
        "captions": [
            {"id": cap["id"], "first_line_chars": len(cap["first_line"]),
             "body_chars": len(cap["body"]), "alt_text_chars": len(cap["alt_text"]),
             "hashtags": len(cap["hashtags"])}
            for cap in plan["captions"]
        ],
    }


def report(summary):
    captions = summary["captions"]
    first = max(cap["first_line_chars"] for cap in captions)
    body = max(cap["body_chars"] for cap in captions)
    alt = max(cap["alt_text_chars"] for cap in captions)
    return (
        "PASS: Pellory plan validated.\n"
        f"Calendar: {summary['days']} days, {summary['formats'].get('Reel', 0)} Reels, "
        f"{summary['formats'].get('Carousel', 0)} carousels.\n"
        f"Production: {summary['reels']} Reel storyboards, {summary['carousels']} carousel decks, "
        f"{len(captions)} captions, {summary['story_frames']} Story frames.\n"
        f"Longest caption fields: first line {first}/125, body {body}/2200, alt text {alt}/300."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print plan statistics as JSON.")
    parser.add_argument("path", type=Path, nargs="?", default=PLAN_PATH, help="Path to the plan JSON.")
    args = parser.parse_args()
    try:
        plan = load_plan(args.path)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    errors = validate(plan)
    if errors:
        print("FAIL:\n" + "\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    summary = stats(plan)
    print(json.dumps(summary, indent=2) if args.json else report(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
