#!/usr/bin/env python3
"""Lightweight slide layout analyzer using pdfplumber (pure Python, no C deps).

Drop-in replacement for analyze_slides.py. Install: pip install pdfplumber
"""

import pdfplumber
import sys
from collections import defaultdict


def analyze_slide(page, page_num):
    """Analyze a single slide for layout issues."""
    issues = []
    width = page.width
    height = page.height

    # Beamer content area boundaries
    header_y = height * 0.08
    footer_y = height * 0.92
    left_margin = width * 0.04
    right_margin = width * 0.96

    # Extract words with positions
    words = page.extract_words(
        x_tolerance=3, y_tolerance=3,
        keep_blank_chars=False, use_text_flow=False,
        extra_attrs=["size", "fontname", "top", "bottom"]
    )

    # Build lines by grouping words with similar y-coordinates
    lines = []
    if words:
        # Sort by vertical position then horizontal
        sorted_words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))

        current_line_words = [sorted_words[0]]
        for w in sorted_words[1:]:
            # Same line if tops are within 3px
            if abs(w["top"] - current_line_words[-1]["top"]) < 3:
                current_line_words.append(w)
            else:
                text = " ".join(cw["text"] for cw in current_line_words)
                lines.append({
                    "x0": min(cw["x0"] for cw in current_line_words),
                    "x1": max(cw["x1"] for cw in current_line_words),
                    "top": min(cw["top"] for cw in current_line_words),
                    "bottom": max(cw["bottom"] for cw in current_line_words),
                    "text": text,
                })
                current_line_words = [w]

        # Don't forget last line
        if current_line_words:
            text = " ".join(cw["text"] for cw in current_line_words)
            lines.append({
                "x0": min(cw["x0"] for cw in current_line_words),
                "x1": max(cw["x1"] for cw in current_line_words),
                "top": min(cw["top"] for cw in current_line_words),
                "bottom": max(cw["bottom"] for cw in current_line_words),
                "text": text,
            })

    # Check 1: Content below footer (overflow)
    overflow_lines = []
    for line in lines:
        if line["bottom"] > footer_y and line["text"].strip():
            text = line["text"].strip()
            # Exclude page numbers (just a number near bottom-right)
            if text.isdigit() and line["x0"] > width * 0.9:
                continue
            overflow_lines.append(line)

    if overflow_lines:
        texts = [l["text"][:60] for l in overflow_lines]
        bottom = max(l["bottom"] for l in overflow_lines)
        overflow_px = bottom - footer_y
        issues.append({
            "type": "OVERFLOW",
            "severity": "HIGH" if overflow_px > 20 else "MEDIUM",
            "detail": f"Content extends {overflow_px:.0f}px below footer area",
            "lines": texts,
        })

    # Check 2: Text overlap (vertical)
    sorted_lines = sorted(lines, key=lambda l: l["top"])
    for i in range(len(sorted_lines) - 1):
        curr = sorted_lines[i]
        nxt = sorted_lines[i + 1]

        # Check horizontal overlap (not side-by-side columns)
        h_overlap = min(curr["x1"], nxt["x1"]) - max(curr["x0"], nxt["x0"])
        if h_overlap < 10:
            continue

        # Check vertical overlap (higher threshold than PyMuPDF version
        # because pdfplumber places math sub/superscripts as separate lines)
        v_overlap = curr["bottom"] - nxt["top"]
        if v_overlap > 8:
            curr_text = curr["text"][:40]
            nxt_text = nxt["text"][:40]
            if curr_text.strip() and nxt_text.strip():
                issues.append({
                    "type": "TEXT_OVERLAP",
                    "severity": "HIGH" if v_overlap > 5 else "MEDIUM",
                    "detail": f"Vertical overlap of {v_overlap:.1f}px between lines",
                    "lines": [f'"{curr_text}" overlaps with "{nxt_text}"'],
                })

    # Check 3: Right margin violations
    for line in lines:
        if line["text"].strip() and line["x1"] > right_margin + 5:
            issues.append({
                "type": "RIGHT_MARGIN",
                "severity": "LOW",
                "detail": f"Text extends {line['x1'] - right_margin:.0f}px past right margin",
                "lines": [line["text"][:50]],
            })

    # Check 4: Content density
    total_text = " ".join(l["text"] for l in lines)
    word_count = len(total_text.split())
    if word_count > 150:
        issues.append({
            "type": "DENSE",
            "severity": "MEDIUM" if word_count < 200 else "HIGH",
            "detail": f"{word_count} words on this slide",
            "lines": [],
        })

    # Check 5: Image sizing (pdfplumber exposes images)
    for img in page.images:
        img_w = img["x1"] - img["x0"]
        img_h = img["bottom"] - img["top"]
        img_area = img_w * img_h
        page_area = width * height
        if img_area / page_area > 0.6:
            issues.append({
                "type": "LARGE_IMAGE",
                "severity": "LOW",
                "detail": f"Image occupies {img_area / page_area * 100:.0f}% of slide",
                "lines": [],
            })

    return issues, word_count


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "slides.pdf"

    pdf = pdfplumber.open(pdf_path)
    print(f"Analyzing {pdf_path}: {len(pdf.pages)} slides\n")
    print("=" * 80)

    total_issues = defaultdict(int)
    slides_with_issues = []

    for i, page in enumerate(pdf.pages):
        page_num = i + 1
        issues, word_count = analyze_slide(page, page_num)

        # Get slide title (first large text)
        title = ""
        words = page.extract_words(extra_attrs=["size"])
        for w in words:
            if w.get("size", 0) > 10:
                title = w["text"][:50]
                break

        # Deduplicate and filter
        seen_overlaps = set()
        deduped = []
        for issue in issues:
            if issue["type"] == "TEXT_OVERLAP":
                key = tuple(issue["lines"])
                if key in seen_overlaps:
                    continue
                seen_overlaps.add(key)
            deduped.append(issue)
        issues = deduped

        if issues:
            slides_with_issues.append(page_num)
            print(f"\nSlide {page_num}: {title}")
            print(f"  Words: {word_count}")
            for issue in issues:
                total_issues[issue["type"]] += 1
                marker = {"HIGH": "\U0001f534", "MEDIUM": "\U0001f7e1", "LOW": "\u26aa"}.get(
                    issue["severity"], "  "
                )
                print(f"  {marker} [{issue['type']}] {issue['detail']}")
                for line in issue.get("lines", [])[:2]:
                    print(f"      \u2192 {line}")
        else:
            print(f"\nSlide {page_num}: {title}  \u2705 ({word_count} words)")

    print("\n" + "=" * 80)
    print(f"\nSUMMARY:")
    print(f"  Total slides: {len(pdf.pages)}")
    print(f"  Slides with issues: {len(slides_with_issues)} ({', '.join(map(str, slides_with_issues))})")
    print(f"  Issue breakdown:")
    for itype, count in sorted(total_issues.items(), key=lambda x: -x[1]):
        print(f"    {itype}: {count}")

    pdf.close()


if __name__ == "__main__":
    main()
