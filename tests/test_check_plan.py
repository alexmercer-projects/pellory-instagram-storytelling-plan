import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.check_plan import load_plan, stats, validate


class CheckPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_plan()

    def assert_error(self, expected):
        errors = validate(self.plan)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_shipped_plan_passes(self):
        self.assertEqual(validate(self.plan), [])
        self.assertEqual(stats(self.plan)["formats"]["Reel"], 12)

    def test_calendar_count(self):
        self.plan["calendar"].pop()
        self.assert_error("Calendar must contain 30 entries")

    def test_reel_count(self):
        self.plan["reels"].pop()
        self.assert_error("Reels must contain 6 entries")

    def test_carousel_count(self):
        self.plan["carousels"].pop()
        self.assert_error("Carousels must contain 3 entries")

    def test_caption_count(self):
        self.plan["captions"].pop()
        self.assert_error("Captions must contain 9 entries")

    def test_story_count(self):
        self.plan["stories"]["frames"].pop()
        self.assert_error("Story frames must contain 7 entries")

    def test_day_numbers_must_be_unique_and_in_range(self):
        for bad_number in (1, 31, True):
            with self.subTest(bad_number=bad_number):
                self.plan["calendar"][-1]["day"] = bad_number
                self.assert_error("day numbers must be unique and cover 1 to 30")

    def test_weekday_follows_monday_start(self):
        self.plan["calendar"][0]["weekday"] = "Sun"
        self.assert_error("weekday must follow the Monday start")

    def test_all_reference_types_are_checked(self):
        mutations = [
            ("calendar", 0, "pillar"),
            ("calendar", 0, "reel_id"),
            ("calendar", 2, "carousel_id"),
            ("reels", 0, "pillar"),
            ("reels", 0, "caption_id"),
            ("carousels", 0, "pillar"),
            ("carousels", 0, "caption_id"),
        ]
        for collection, index, field in mutations:
            with self.subTest(collection=collection, field=field):
                self.plan = load_plan()
                self.plan[collection][index][field] = "missing"
                self.assert_error(f"{field} references unknown ID 'missing'")

    def test_caption_can_only_be_used_once(self):
        self.plan["reels"][1]["caption_id"] = self.plan["reels"][0]["caption_id"]
        self.assert_error("must be used by exactly one Reel or Carousel")

    def test_reel_shot_timing_can_have_no_gaps_or_overlaps(self):
        for value in (1, 4):
            with self.subTest(value=value):
                self.plan["reels"][0]["shots"][1]["start_s"] = value
                self.assert_error("timings must be contiguous from 0")

    def test_reel_shot_timing_starts_at_zero(self):
        self.plan["reels"][0]["shots"][0]["start_s"] = 1
        self.assert_error("timings must be contiguous from 0")

    def test_reel_shot_timing_ends_at_reel_length(self):
        self.plan["reels"][0]["shots"][-1]["end_s"] -= 1
        self.assert_error("shots must end at length_s")

    def test_reel_shot_count_and_length(self):
        self.plan["reels"][0]["length_s"] = 60
        self.plan["reels"][0]["shots"] = []
        self.assert_error("length_s must be 15 to 45 seconds")
        self.assert_error("shots must contain 4 to 8 entries")

    def test_carousel_slide_count(self):
        self.plan["carousels"][0]["slides"] = []
        self.assert_error("slides must contain 5 to 7 entries")

    def test_first_line_length(self):
        self.plan["captions"][0]["first_line"] = "x" * 126
        self.assert_error("first_line must be one non-empty line of at most 125 characters")

    def test_first_line_must_match_body(self):
        self.plan["captions"][0]["body"] = "Different hook."
        self.assert_error("first_line must be the start of its body")

    def test_body_length(self):
        self.plan["captions"][0]["body"] += "x" * 2201
        self.assert_error("body must be non-empty and at most 2200 characters")

    def test_hashtag_count(self):
        for count in (2, 6):
            with self.subTest(count=count):
                self.plan["captions"][0]["hashtags"] = [f"#tag{i}" for i in range(count)]
                self.assert_error("must have 3 to 5 hashtags")

    def test_hashtag_syntax_and_case(self):
        for tag in ("missinghash", "#Uppercase", "#with space", "#"):
            with self.subTest(tag=tag):
                self.plan["captions"][0]["hashtags"][0] = tag
                self.assert_error("hashtags must be lowercase, start with # and contain no spaces")

    def test_duplicate_hashtags(self):
        tags = self.plan["captions"][0]["hashtags"]
        tags[1] = tags[0]
        self.assert_error("contains duplicate hashtags")

    def test_alt_text_is_present_and_within_limit(self):
        for text in ("", " ", "x" * 301):
            with self.subTest(text=text[:12]):
                self.plan["captions"][0]["alt_text"] = text
                self.assert_error("alt_text is required and must be at most 300 characters")
        del self.plan["captions"][0]["alt_text"]
        self.assert_error("alt_text is required")

    def test_prose_dashes_are_rejected_even_in_nested_strings(self):
        for text in ("Clay\u2014then water", "Clay \u2013 then water"):
            with self.subTest(text=text):
                self.plan["stories"]["frames"][1]["sticker"][0] = text
                self.assert_error("contains an em dash or an en dash used as a dash")

    def test_phone_format_is_checked_in_free_copy(self):
        for number in ("555-0142", "(303) 555-0177", "303.555.0177", "+1 303 555 0177"):
            with self.subTest(number=number):
                self.plan["stories"]["frames"][0]["text"] = f"Call {number}."
                self.assert_error("phone number must use (555) 01xx")

    def test_email_domain_is_checked_in_free_copy(self):
        for email in ("june@other.test", "june@example.com.other.test"):
            with self.subTest(email=email):
                self.plan["stories"]["frames"][0]["text"] = f"Write to {email}."
                self.assert_error("email address must end in @example.com")

    def test_pillar_shares(self):
        self.plan["pillars"][0]["share"] -= 1
        self.assert_error("shares must be whole percentages that sum to 100")

    def test_cli_json_reports_caption_lengths(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "check_plan.py"
        result = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=True)
        summary = json.loads(result.stdout)
        self.assertEqual(summary, stats(self.plan))

    def test_cli_fails_with_a_locatable_error(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "check_plan.py"
        self.plan["calendar"][1]["day"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-plan.json"
            path.write_text(json.dumps(self.plan), encoding="utf-8")
            result = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Calendar day numbers must be unique", result.stderr)


if __name__ == "__main__":
    unittest.main()
