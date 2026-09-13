"""tests/test_reasoning.py — Unit tests for the reasoning layer."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from app.reasoning import answer_question, classify_intent


# Sample detections for testing
DETECTIONS_FULL = [
    {"class": "forklift", "confidence": 0.91, "bbox": {"x1": 100, "y1": 80, "x2": 400, "y2": 350}},
    {"class": "forklift", "confidence": 0.85, "bbox": {"x1": 450, "y1": 100, "x2": 700, "y2": 380}},
    {"class": "wood pallet", "confidence": 0.78, "bbox": {"x1": 50, "y1": 300, "x2": 250, "y2": 450}},
    {"class": "truck", "confidence": 0.62, "bbox": {"x1": 500, "y1": 200, "x2": 900, "y2": 500}},
    {"class": "cardboard box", "confidence": 0.55, "bbox": {"x1": 10, "y1": 10, "x2": 80, "y2": 60}},
]

DETECTIONS_LOW_CONF = [
    {"class": "forklift", "confidence": 0.18, "bbox": {"x1": 100, "y1": 80, "x2": 400, "y2": 350}},
]

DETECTIONS_EMPTY = []


# ── Intent classification ─────────────────────────────────────────────────────

class TestIntentClassification:
    def test_count_intent(self):
        assert classify_intent("How many forklifts are visible?") == "COUNT"
        assert classify_intent("What is the number of trucks?") == "COUNT"

    def test_presence_intent(self):
        assert classify_intent("Is there a forklift?") == "PRESENCE"
        assert classify_intent("Are there any trucks visible?") == "PRESENCE"

    def test_list_intent(self):
        assert classify_intent("What objects are in the image?") == "LIST"
        assert classify_intent("Which objects can you see?") == "LIST"

    def test_most_common_intent(self):
        assert classify_intent("What is the most common object?") == "MOST_COMMON"

    def test_spatial_intent(self):
        assert classify_intent("Is the forklift near the pallet?") == "SPATIAL"
        assert classify_intent("Is the truck to the left of the container?") == "SPATIAL"

    def test_unknown_intent(self):
        assert classify_intent("What is the weather like?") == "UNKNOWN"
        assert classify_intent("Who built this warehouse?") == "UNKNOWN"


# ── Normal questions ──────────────────────────────────────────────────────────

class TestNormalQuestions:
    def test_count_forklifts(self):
        result = answer_question("How many forklifts are visible?", DETECTIONS_FULL)
        assert "2" in result["answer"] or "two" in result["answer"].lower()
        assert result["used_detector"] is True
        assert result["confidence"] in ("high", "medium")

    def test_count_trucks(self):
        result = answer_question("How many trucks are in the image?", DETECTIONS_FULL)
        assert "1" in result["answer"] or "one" in result["answer"].lower()
        assert result["used_detector"] is True

    def test_presence_forklift_yes(self):
        result = answer_question("Is there a forklift?", DETECTIONS_FULL)
        assert "yes" in result["answer"].lower() or "forklift" in result["answer"].lower()
        assert result["confidence"] in ("high", "medium")

    def test_presence_container_no(self):
        result = answer_question("Is there a freight container?", DETECTIONS_FULL)
        assert "no" in result["answer"].lower() or "not detected" in result["answer"].lower()

    def test_list_objects(self):
        result = answer_question("What objects are in the image?", DETECTIONS_FULL)
        assert "forklift" in result["answer"].lower()
        assert result["used_detector"] is True

    def test_most_common(self):
        result = answer_question("What is the most common object?", DETECTIONS_FULL)
        assert "forklift" in result["answer"].lower()

    def test_is_more_than_one_truck(self):
        result = answer_question("Is there more than one truck?", DETECTIONS_FULL)
        assert result["used_detector"] is True


# ── Unrelated questions ───────────────────────────────────────────────────────

class TestUnrelatedQuestions:
    def test_weather_question(self):
        result = answer_question("What is the weather today?", DETECTIONS_FULL)
        assert result["intent"] == "UNKNOWN"
        assert result["used_detector"] is False

    def test_random_question(self):
        result = answer_question("Who is the CEO?", DETECTIONS_EMPTY)
        assert result["intent"] == "UNKNOWN"
        assert result["confidence"] == "low"


# ── Confidence guardrail ──────────────────────────────────────────────────────

class TestConfidenceGuardrail:
    def test_low_confidence_detection(self):
        # conf=0.18 < LOW_CONF_THRESHOLD (0.25) → guardrail returns 'low'
        result = answer_question("How many forklifts are visible?", DETECTIONS_LOW_CONF)
        assert result["confidence"] == "low", (
            f"Expected 'low' confidence for conf=0.18, got '{result['confidence']}'"
        )
        # Answer should acknowledge insufficient confidence
        assert (
            "insufficient" in result["answer"].lower()
            or "confident" in result["answer"].lower()
            or "low" in result["answer"].lower()
        )

    def test_low_confidence_presence(self):
        # PRESENCE with conf=0.18: matching exists but below floor → 'low'
        result = answer_question("Is there a forklift?", DETECTIONS_LOW_CONF)
        assert result["confidence"] == "low", (
            f"Expected 'low' confidence for conf=0.18, got '{result['confidence']}'"
        )

    def test_no_detections(self):
        result = answer_question("Is there a forklift?", DETECTIONS_EMPTY)
        assert result["confidence"] == "low"
        assert result["used_detector"] is True

    def test_count_no_detections(self):
        result = answer_question("How many trucks are visible?", DETECTIONS_EMPTY)
        assert result["confidence"] == "low"


# ── Spatial questions ─────────────────────────────────────────────────────────

class TestSpatialQuestions:
    def test_forklift_near_pallet(self):
        result = answer_question("Is the forklift near the pallet?", DETECTIONS_FULL)
        assert result["used_detector"] is True
        assert result["confidence"] in ("high", "medium", "low")
        assert len(result["answer"]) > 0

    def test_spatial_missing_class(self):
        result = answer_question("Is the forklift near the container?", DETECTIONS_FULL)
        # No container in detections → low confidence
        assert result["confidence"] == "low"


# ── Ambiguous questions ───────────────────────────────────────────────────────

class TestAmbiguousQuestions:
    def test_ambiguous_count(self):
        # "How many" without a class name → count all
        result = answer_question("How many objects are there?", DETECTIONS_FULL)
        assert result["used_detector"] is True
        assert str(len(DETECTIONS_FULL)) in result["answer"] or "5" in result["answer"]

    def test_presence_without_class(self):
        result = answer_question("Are there any objects in this image?", DETECTIONS_FULL)
        assert result["used_detector"] is True
