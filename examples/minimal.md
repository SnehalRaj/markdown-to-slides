---
title: "My Presentation"
subtitle: "A Quick Example"
author: "Your Name"
date: "March 2026"
theme: "metropolis"
classoption: "aspectratio=169"
header-includes:
  - \usepackage{booktabs}
  - \usepackage{amsmath,amssymb}
  - \setbeamertemplate{navigation symbols}{}
  - \setbeamerfont{normal text}{size=\small}
  - \AtBeginDocument{\usebeamerfont{normal text}}
---

## Introduction

- This is a minimal example
- Write slides in **plain Markdown**
- Compile with one `pandoc` command

---

## Math Works Natively

The Cauchy-Schwarz inequality:

$$\left| \langle u, v \rangle \right|^2 \leq \langle u, u \rangle \cdot \langle v, v \rangle$$

---

## Tables Too

| Method | Complexity | Notes |
|--------|-----------|-------|
| Brute force | $O(n^2)$ | Baseline |
| Divide & conquer | $O(n \log n)$ | Standard |
| Linear | $O(n)$ | Optimal |

---

## Images

![Description of figure](path/to/figure.png){width=70%}

Adjust `width` percentage if the analyzer flags overflow.

---

## Summary

1. Write markdown with YAML frontmatter
2. Compile: `pandoc slides.md -t beamer --pdf-engine=pdflatex -o slides.pdf`
3. Analyze: `python tools/analyze_slides.py slides.pdf`
4. Fix issues, repeat until clean
