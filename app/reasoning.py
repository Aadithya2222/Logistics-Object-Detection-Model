"""
app/reasoning.py

Hand-written deterministic intent router and reasoning layer.
NO LangChain / LangGraph / CrewAI / AutoGen — pure Python logic.

Supported intents:
    COUNT        — "how many", "number of", "count"
    PRESENCE     — "is there", "are there", "does the image contain", "is a"
    LIST         — "what objects", "which objects", "what is in"
    MOST_COMMON  — "most common", "most frequent", "dominant"
    SPATIAL      — "near", "next to", "left of", "right of", "above", "below"
    UNKNOWN      — anything not matched above
"""

import re
from collections import Counter
from typing import Literal

from app.utils import box_distance, boxes_overlap, relative_position

CLASS_NAMES = [
    "cardboard box",
    "forklift",
    "freight container",
    "wood pallet",
    "truck",
]

# Confidence guardrail thresholds
HIGH_CONF_THRESHOLD = 0.50
LOW_CONF_THRESHOLD = 0.25

Intent = Literal["COUNT", "PRESENCE", "LIST", "MOST_COMMON", "SPATIAL", "UNKNOWN"]


# ── Intent classification ─────────────────────────────────────────────────────

COUNT_PATTERNS = re.compile(
    r"how many|number of|count of|total number|how much",
    re.IGNORECASE,
)
PRESENCE_PATTERNS = re.compile(
    r"is there\b|are there\b|does the image contain|is a\b|is an\b|"
    r"can you see|do you see|is it present|is .+ visible|are .+ visible",
    re.IGNORECASE,
)
LIST_PATTERNS = re.compile(
    r"what objects|which objects|what is in|what are in|list .+ objects|"
    r"what can you see|what do you see|identify|what.s in",
    re.IGNORECASE,
)
MOST_COMMON_PATTERNS = re.compile(
    r"most common|most frequent|dominant object|most .+ object",
    re.IGNORECASE,
)
SPATIAL_PATTERNS = re.compile(
    r"\bnear\b|\bnext to\b|\bleft of\b|\bright of\b|\babove\b|\bbelow\b|"
    r"\bbeside\b|\badjacent\b|\bclose to\b",
    re.IGNORECASE,
)


def classify_intent(question: str) -> Intent:
    """Map a natural-language question to a deterministic intent label."""
    q = question.strip()
    if COUNT_PATTERNS.search(q):
        return "COUNT"
    if MOST_COMMON_PATTERNS.search(q):
        return "MOST_COMMON"
    if LIST_PATTERNS.search(q):
        return "LIST"
    if SPATIAL_PATTERNS.search(q):
        return "SPATIAL"
    if PRESENCE_PATTERNS.search(q):
        return "PRESENCE"
    return "UNKNOWN"


# ── Class extraction from question ───────────────────────────────────────────

# Also accept plural forms and common synonyms
CLASS_ALIASES = {
    "cardboard box": ["cardboard box", "cardboard boxes", "box", "boxes", "carton", "cartons"],
    "forklift": ["forklift", "forklifts", "fork lift", "fork lifts"],
    "freight container": [
        "freight container", "freight containers", "container", "containers",
        "shipping container", "shipping containers", "cargo container",
    ],
    "wood pallet": [
        "wood pallet", "wood pallets", "wooden pallet", "wooden pallets",
        "pallet", "pallets",
    ],
    "truck": ["truck", "trucks", "lorry", "lorries", "semi truck", "semi trucks"],
}


def extract_class(question: str) -> str | None:
    """Return the canonical class name mentioned in the question, or None."""
    q_lower = question.lower()
    for canonical, aliases in CLASS_ALIASES.items():
        for alias in aliases:
            if alias in q_lower:
                return canonical
    return None


# ── Confidence guardrail ──────────────────────────────────────────────────────

def detection_confidence_level(
    detections: list[dict],
    target_class: str | None = None,
) -> Literal["high", "medium", "low"]:
    """
    Compute a confidence label for the detection result.

    Rules:
    - No detections at all → low
    - If target_class specified:
        - No matching detection → low
        - Max conf of matching detections ≥ HIGH_CONF_THRESHOLD → high
        - Max conf ≥ LOW_CONF_THRESHOLD → medium
        - Max conf < LOW_CONF_THRESHOLD → low (below guardrail floor)
    - If no target_class:
        - All detections ≥ HIGH_CONF_THRESHOLD → high
        - Any detection ≥ LOW_CONF_THRESHOLD → medium
        - All below LOW_CONF_THRESHOLD → low
    """
    if not detections:
        return "low"

    if target_class:
        matching = [d for d in detections if d["class"] == target_class]
        if not matching:
            return "low"
        max_conf = max(d["confidence"] for d in matching)
        if max_conf >= HIGH_CONF_THRESHOLD:
            return "high"
        if max_conf >= LOW_CONF_THRESHOLD:
            return "medium"
        return "low"  # Below guardrail floor — insufficient evidence
    else:
        confs = [d["confidence"] for d in detections]
        if all(c >= HIGH_CONF_THRESHOLD for c in confs):
            return "high"
        if any(c >= LOW_CONF_THRESHOLD for c in confs):
            return "medium"
        return "low"


# ── Reasoning functions ───────────────────────────────────────────────────────

def reason_count(detections: list[dict], question: str) -> dict:
    target_class = extract_class(question)

    if not detections:
        return {
            "answer": "No objects were detected in the image.",
            "used_detector": True,
            "confidence": "low",
        }

    if target_class:
        matching = [d for d in detections if d["class"] == target_class]
        count = len(matching)
        conf = detection_confidence_level(detections, target_class)
        if conf == "low":
            return {
                "answer": (
                    f"I could not confidently detect any {target_class} in the image. "
                    "Insufficient information to answer confidently."
                ),
                "used_detector": True,
                "confidence": "low",
            }
        plural = "s" if count != 1 else ""
        return {
            "answer": f"There {'is' if count == 1 else 'are'} {count} {target_class}{plural} visible.",
            "used_detector": True,
            "confidence": conf,
        }
    else:
        # Count all classes
        counter = Counter(d["class"] for d in detections)
        parts = [f"{v} {k}{'s' if v != 1 else ''}" for k, v in counter.items()]
        answer = f"Detected: {', '.join(parts)}. Total: {len(detections)} object(s)."
        return {
            "answer": answer,
            "used_detector": True,
            "confidence": detection_confidence_level(detections),
        }


def reason_presence(detections: list[dict], question: str) -> dict:
    target_class = extract_class(question)

    if not detections:
        return {
            "answer": "No objects were detected in the image.",
            "used_detector": True,
            "confidence": "low",
        }

    if target_class:
        matching = [d for d in detections if d["class"] == target_class]
        conf = detection_confidence_level(detections, target_class)
        if matching:
            max_conf = max(d["confidence"] for d in matching)
            if conf == "low":
                return {
                    "answer": (
                        f"A {target_class} may be present, but confidence is low ({max_conf:.2f}). "
                        "Insufficient information to answer confidently."
                    ),
                    "used_detector": True,
                    "confidence": "low",
                }
            return {
                "answer": f"Yes, there {'is' if len(matching) == 1 else 'are'} "
                          f"{len(matching)} {target_class}{'s' if len(matching) != 1 else ''} visible.",
                "used_detector": True,
                "confidence": conf,
            }
        else:
            return {
                "answer": f"No {target_class} was detected in the image.",
                "used_detector": True,
                "confidence": "high" if detections else "low",
            }
    else:
        classes_present = sorted(set(d["class"] for d in detections))
        answer = f"Yes, the image contains: {', '.join(classes_present)}."
        return {
            "answer": answer,
            "used_detector": True,
            "confidence": detection_confidence_level(detections),
        }


def reason_list(detections: list[dict], question: str) -> dict:
    if not detections:
        return {
            "answer": "No objects were detected in the image.",
            "used_detector": True,
            "confidence": "low",
        }

    counter = Counter(d["class"] for d in detections)
    parts = [f"{v}× {k}" for k, v in sorted(counter.items())]
    return {
        "answer": f"Objects in the image: {', '.join(parts)}.",
        "used_detector": True,
        "confidence": detection_confidence_level(detections),
    }


def reason_most_common(detections: list[dict], question: str) -> dict:
    if not detections:
        return {
            "answer": "No objects were detected in the image.",
            "used_detector": True,
            "confidence": "low",
        }

    counter = Counter(d["class"] for d in detections)
    most_common_cls, count = counter.most_common(1)[0]
    plural = "s" if count != 1 else ""
    return {
        "answer": f"The most common object is '{most_common_cls}' with {count} instance{plural}.",
        "used_detector": True,
        "confidence": detection_confidence_level(detections),
    }


def reason_spatial(detections: list[dict], question: str) -> dict:
    """
    Handle spatial queries like 'is the forklift near the pallet?'
    Extract two class names from the question and compute their spatial relationship.
    """
    q_lower = question.lower()

    # Find all mentioned classes
    mentioned = []
    for canonical, aliases in CLASS_ALIASES.items():
        for alias in aliases:
            if alias in q_lower:
                mentioned.append(canonical)
                break

    if not detections:
        return {
            "answer": "No objects were detected in the image.",
            "used_detector": True,
            "confidence": "low",
        }

    if len(mentioned) < 2:
        # Only one class mentioned — describe its position
        target = mentioned[0] if mentioned else None
        if not target:
            return {
                "answer": "Could not identify which objects to compare spatially.",
                "used_detector": True,
                "confidence": "low",
            }
        matching = [d for d in detections if d["class"] == target]
        if not matching:
            return {
                "answer": f"No {target} detected. Cannot determine spatial relationship.",
                "used_detector": True,
                "confidence": "low",
            }
        return {
            "answer": f"Found {len(matching)} {target}(s) in the image, but no second object specified for comparison.",
            "used_detector": True,
            "confidence": "medium",
        }

    class_a, class_b = mentioned[0], mentioned[1]
    items_a = [d for d in detections if d["class"] == class_a]
    items_b = [d for d in detections if d["class"] == class_b]

    if not items_a or not items_b:
        missing = []
        if not items_a:
            missing.append(class_a)
        if not items_b:
            missing.append(class_b)
        return {
            "answer": (
                f"Could not find {'both' if len(missing) == 2 else ''} "
                f"{' and '.join(missing)} in the image. "
                "Insufficient information to answer confidently."
            ),
            "used_detector": True,
            "confidence": "low",
        }

    # Use the highest-confidence detection of each class
    a = max(items_a, key=lambda d: d["confidence"])
    b = max(items_b, key=lambda d: d["confidence"])

    dist = box_distance(a["bbox"], b["bbox"])
    overlap_iou = boxes_overlap(a["bbox"], b["bbox"])
    rel_pos = relative_position(a["bbox"], b["bbox"])

    NEAR_THRESHOLD = 150  # pixels

    if overlap_iou > 0.05:
        spatial_desc = f"The {class_a} and {class_b} are overlapping or very close together."
    elif dist < NEAR_THRESHOLD:
        spatial_desc = f"The {class_a} is near the {class_b} (distance ≈ {dist:.0f}px)."
    else:
        spatial_desc = (
            f"The {class_a} is {rel_pos} the {class_b} "
            f"(distance ≈ {dist:.0f}px, not immediately adjacent)."
        )

    conf = detection_confidence_level(detections, class_a)
    if conf == "high" and detection_confidence_level(detections, class_b) != "high":
        conf = "medium"

    return {
        "answer": spatial_desc,
        "used_detector": True,
        "confidence": conf,
    }


def reason_unknown(question: str) -> dict:
    return {
        "answer": (
            "I can only answer questions about the five detected object classes: "
            "cardboard box, forklift, freight container, wood pallet, and truck. "
            "Please ask about counting, presence, or spatial relationships between these objects."
        ),
        "used_detector": False,
        "confidence": "low",
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def answer_question(question: str, detections: list[dict]) -> dict:
    """
    Route a natural-language question to the appropriate reasoning function
    and return a structured response.

    Args:
        question: Natural-language question string
        detections: List of detection dicts from RTDETRDetector.detect()

    Returns:
        {
            "answer": str,
            "used_detector": bool,
            "confidence": "high" | "medium" | "low",
            "intent": str,
        }
    """
    intent = classify_intent(question)

    if intent == "COUNT":
        result = reason_count(detections, question)
    elif intent == "PRESENCE":
        result = reason_presence(detections, question)
    elif intent == "LIST":
        result = reason_list(detections, question)
    elif intent == "MOST_COMMON":
        result = reason_most_common(detections, question)
    elif intent == "SPATIAL":
        result = reason_spatial(detections, question)
    else:
        result = reason_unknown(question)

    result["intent"] = intent
    return result
