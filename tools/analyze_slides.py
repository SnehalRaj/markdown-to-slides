#!/usr/bin/env python3
"""Analyze beamer PDF slides for overflow, text overlap, and spacing issues."""

import fitz  # PyMuPDF
import sys
from collections import defaultdict


def analyze_slide(page, page_num):
    """Analyze a single slide for layout issues."""
    issues = []
    width = page.rect.width
    height = page.rect.height

    # Extract all text blocks: (x0, y0, x1, y1, text, block_no, block_type)
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    # Beamer slides have a content area. The header bar is ~top 8%,
    # footer/page number is ~bottom 5%. Content area is roughly 8%-95% of height.
    header_y = height * 0.08
    footer_y = height * 0.92
    left_margin = width * 0.04
    right_margin = width * 0.96

    all_spans = []
    all_lines = []
    all_block_rects = []

    for block in blocks["blocks"]:
        if block["type"] != 0:  # text block
            continue

        block_rect = fitz.Rect(block["bbox"])
        all_block_rects.append(block_rect)

        for line in block["lines"]:
            line_rect = fitz.Rect(line["bbox"])
            line_text = ""
            for span in line["spans"]:
                line_text += span["text"]
                all_spans.append({
                    "rect": fitz.Rect(span["bbox"]),
                    "text": span["text"],
                    "size": span["size"],
                    "font": span["font"],
                })
            all_lines.append({
                "rect": line_rect,
                "text": line_text.strip(),
            })

    # Check 1: Content below footer (overflow)
    overflow_lines = []
    for line in all_lines:
        if line["rect"].y1 > footer_y and line["text"].strip():
            # Exclude page numbers (typically just a number near bottom-right)
            text = line["text"].strip()
            if text.isdigit() and line["rect"].x0 > width * 0.9:
                continue
            overflow_lines.append(line)

    if overflow_lines:
        texts = [l["text"][:60] for l in overflow_lines]
        bottom_y = max(l["rect"].y1 for l in overflow_lines)
        overflow_px = bottom_y - footer_y
        issues.append({
            "type": "OVERFLOW",
            "severity": "HIGH" if overflow_px > 20 else "MEDIUM",
            "detail": f"Content extends {overflow_px:.0f}px below footer area",
            "lines": texts,
        })

    # Check 2: Text overlap (vertical)
    # Sort lines by vertical position
    sorted_lines = sorted(all_lines, key=lambda l: l["rect"].y0)
    for i in range(len(sorted_lines) - 1):
        curr = sorted_lines[i]
        next_line = sorted_lines[i + 1]

        # Check if lines are in the same horizontal region (not side-by-side columns)
        h_overlap = min(curr["rect"].x1, next_line["rect"].x1) - max(curr["rect"].x0, next_line["rect"].x0)
        if h_overlap < 10:
            continue  # Side-by-side, not overlapping

        # Check vertical overlap
        v_overlap = curr["rect"].y1 - next_line["rect"].y0
        if v_overlap > 2:  # More than 2px overlap
            curr_text = curr["text"][:40]
            next_text = next_line["text"][:40]
            if curr_text.strip() and next_text.strip():
                issues.append({
                    "type": "TEXT_OVERLAP",
                    "severity": "HIGH" if v_overlap > 5 else "MEDIUM",
                    "detail": f"Vertical overlap of {v_overlap:.1f}px between lines",
                    "lines": [f'"{curr_text}" overlaps with "{next_text}"'],
                })

    # Check 3: Content too close to margins
    for line in all_lines:
        if line["text"].strip() and line["rect"].x1 > right_margin + 5:
            issues.append({
                "type": "RIGHT_MARGIN",
                "severity": "LOW",
                "detail": f"Text extends {line['rect'].x1 - right_margin:.0f}px past right margin",
                "lines": [line["text"][:50]],
            })

    # Check 4: Table cell cramping (detect very small line spacing in table-like areas)
    # Look for consecutive lines with very tight spacing
    for i in range(len(sorted_lines) - 1):
        curr = sorted_lines[i]
        next_line = sorted_lines[i + 1]

        h_overlap = min(curr["rect"].x1, next_line["rect"].x1) - max(curr["rect"].x0, next_line["rect"].x0)
        if h_overlap < 10:
            continue

        gap = next_line["rect"].y0 - curr["rect"].y1
        line_height = curr["rect"].y1 - curr["rect"].y0

        if 0 < gap < 1 and line_height > 5:  # Very tight but not overlapping
            curr_text = curr["text"][:40]
            next_text = next_line["text"][:40]
            if curr_text.strip() and next_text.strip():
                issues.append({
                    "type": "TIGHT_SPACING",
                    "severity": "LOW",
                    "detail": f"Only {gap:.1f}px gap between lines (line height: {line_height:.0f}px)",
                    "lines": [f'"{curr_text}" → "{next_text}"'],
                })

    # Check 5: Content density (too much text per slide)
    total_text = " ".join(l["text"] for l in all_lines)
    word_count = len(total_text.split())
    if word_count > 150:
        issues.append({
            "type": "DENSE",
            "severity": "MEDIUM" if word_count < 200 else "HIGH",
            "detail": f"{word_count} words on this slide",
            "lines": [],
        })

    # Check 6: Image sizing issues
    for block in blocks["blocks"]:
        if block["type"] == 1:  # image block
            img_rect = fitz.Rect(block["bbox"])
            img_area = img_rect.width * img_rect.height
            page_area = width * height
            if img_area / page_area > 0.6:
                issues.append({
                    "type": "LARGE_IMAGE",
                    "severity": "LOW",
                    "detail": f"Image occupies {img_area/page_area*100:.0f}% of slide",
                    "lines": [],
                })

    return issues, word_count


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "slides/research_progress.pdf"
    doc = fitz.open(pdf_path)

    print(f"Analyzing {pdf_path}: {len(doc)} slides\n")
    print("=" * 80)

    total_issues = defaultdict(int)
    slides_with_issues = []

    for i, page in enumerate(doc):
        page_num = i + 1
        issues, word_count = analyze_slide(page, page_num)

        # Get slide title from first text block
        blocks = page.get_text("dict")["blocks"]
        title = ""
        for block in blocks:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > 10:  # Title font is larger
                            title = span["text"][:50]
                            break
                    if title:
                        break
            if title:
                break

        # Deduplicate text overlap issues (keep worst per pair)
        seen_overlaps = set()
        deduped = []
        for issue in issues:
            if issue["type"] == "TEXT_OVERLAP":
                key = tuple(issue["lines"])
                if key in seen_overlaps:
                    continue
                seen_overlaps.add(key)
            # Skip LOW tight spacing (too noisy)
            if issue["type"] == "TIGHT_SPACING":
                continue
            deduped.append(issue)
        issues = deduped

        if issues:
            slides_with_issues.append(page_num)
            print(f"\nSlide {page_num}: {title}")
            print(f"  Words: {word_count}")
            for issue in issues:
                total_issues[issue["type"]] += 1
                severity_marker = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪"}.get(issue["severity"], "  ")
                print(f"  {severity_marker} [{issue['type']}] {issue['detail']}")
                for line in issue.get("lines", [])[:2]:  # Show max 2 example lines
                    print(f"      → {line}")
        else:
            # Print clean slides too for completeness
            print(f"\nSlide {page_num}: {title}  ✅ ({word_count} words)")

    print("\n" + "=" * 80)
    print(f"\nSUMMARY:")
    print(f"  Total slides: {len(doc)}")
    print(f"  Slides with issues: {len(slides_with_issues)} ({', '.join(map(str, slides_with_issues))})")
    print(f"  Issue breakdown:")
    for itype, count in sorted(total_issues.items(), key=lambda x: -x[1]):
        print(f"    {itype}: {count}")

    doc.close()


if __name__ == "__main__":
    main()
