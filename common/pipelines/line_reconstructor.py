import re
from dataclasses import dataclass
from typing import List


@dataclass
class TextLine:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font_size: float | None = None


@dataclass
class Paragraph:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float


class LineReconstructor:

    def __init__(
        self,
        x_threshold: float = 15,
        y_threshold: float = 20,
        indent_threshold: float = 20,
    ):
        self.x_threshold = x_threshold
        self.y_threshold = y_threshold
        self.indent_threshold = indent_threshold

    # ----------------------------
    # Public API
    # ----------------------------
    def reconstruct(self, lines: List[TextLine]) -> List[Paragraph]:
        if not lines:
            return []

        # Step 1: sort top-to-bottom, left-to-right
        lines = sorted(lines, key=lambda l: (l.y0, l.x0))

        paragraphs: List[Paragraph] = []
        current_group = [lines[0]]

        for prev, curr in zip(lines, lines[1:]):
            if self._should_merge(prev, curr):
                current_group.append(curr)
            else:
                paragraphs.append(self._build_paragraph(current_group))
                current_group = [curr]

        paragraphs.append(self._build_paragraph(current_group))
        return paragraphs

    # ----------------------------
    # Merge Logic
    # ----------------------------
    def _should_merge(self, prev: TextLine, curr: TextLine) -> bool:
        vertical_gap = curr.y0 - prev.y1
        x_aligned = abs(curr.x0 - prev.x0) < self.x_threshold

        # bullet continuation
        if self._is_continuation(prev.text, curr.text, curr.x0 - prev.x0):
            return True

        if vertical_gap < self.y_threshold and x_aligned:
            return True

        return False

    def _is_continuation(self, prev_text: str, curr_text: str, indent_diff: float) -> bool:
        # If previous line ends with colon
        if prev_text.strip().endswith(":"):
            return True

        # If current line starts lowercase (sentence continuation)
        if curr_text and curr_text[0].islower():
            return True

        # If indentation suggests continuation
        if indent_diff > self.indent_threshold:
            return True

        # If previous line ends without punctuation
        if not re.search(r"[.!?]$", prev_text.strip()):
            return True

        return False

    # ----------------------------
    # Paragraph Builder
    # ----------------------------
    def _build_paragraph(self, group: List[TextLine]) -> Paragraph:
        merged_text = " ".join(line.text.strip() for line in group)

        x0 = min(line.x0 for line in group)
        y0 = min(line.y0 for line in group)
        x1 = max(line.x1 for line in group)
        y1 = max(line.y1 for line in group)

        confidence = self._confidence_score(group)

        return Paragraph(
            text=merged_text,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            confidence=confidence,
        )

    # ----------------------------
    # Confidence Scoring
    # ----------------------------
    def _confidence_score(self, group: List[TextLine]) -> float:
        text = " ".join(l.text for l in group).strip()

        score = 1.0

        # penalty: ends mid sentence
        if not re.search(r"[.!?]$", text):
            score -= 0.1

        # penalty: too short
        if len(text) < 10:
            score -= 0.1

        # penalty: weird OCR artifacts
        if re.search(r"[^\x00-\x7F]+", text):
            score -= 0.05

        return max(score, 0.0)