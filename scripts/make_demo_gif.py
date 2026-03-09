#!/usr/bin/env python3
"""Generate an animated GIF simulating the md-slides terminal workflow."""
from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 800, 480
BG = (30, 30, 46)        # Dark terminal bg
FG = (205, 214, 244)     # Light text
GREEN = (166, 227, 161)
YELLOW = (249, 226, 175)
RED = (243, 139, 168)
BLUE = (137, 180, 250)
GRAY = (108, 112, 134)
MAUVE = (203, 166, 247)
TITLE_BG = (49, 50, 68)

def get_font(size=16):
    for name in ["/System/Library/Fonts/Menlo.ttc",
                 "/System/Library/Fonts/SFMono-Regular.otf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]:
        if os.path.exists(name):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
    return ImageFont.load_default()

font = get_font(15)
font_bold = get_font(16)

def make_frame(lines):
    """lines: list of (text, color) or (text, color, 'bold')"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    # Title bar
    draw.rectangle([(0, 0), (WIDTH, 32)], fill=TITLE_BG)
    # Window buttons
    for i, c in enumerate([(243,139,168), (249,226,175), (166,227,161)]):
        draw.ellipse([(12 + i*22, 9), (24 + i*22, 21)], fill=c)
    draw.text((WIDTH//2 - 90, 7), "markdown-to-slides demo", fill=GRAY, font=font)

    y = 44
    for entry in lines:
        text = entry[0]
        color = entry[1] if len(entry) > 1 else FG
        f = font_bold if (len(entry) > 2 and entry[2] == 'bold') else font
        draw.text((16, y), text, fill=color, font=f)
        y += 22
    return img

# Build frames as a storyboard
scenes = []

# Scene 1: Show the markdown file
s1 = [
    ("$ cat slides.md", GREEN),
    ("---", GRAY),
    ("title: \"Gradient Descent Demystified\"", YELLOW),
    ("author: \"Your Name\"", YELLOW),
    ("theme: \"metropolis\"", YELLOW),
    ("classoption: \"aspectratio=169\"", YELLOW),
    ("---", GRAY),
    ("", FG),
    ("## The Core Idea", BLUE, "bold"),
    ("", FG),
    ("**Problem:** Find θ* that minimizes L(θ)", FG),
    ("", FG),
    ("$$θ_{t+1} = θ_t - η ∇L(θ_t)$$", MAUVE),
    ("", FG),
    ("- η is the **learning rate**", FG),
    ("- The gradient ∇L points uphill", FG),
]
scenes.append((s1, 2500))

# Scene 2: Compile
s2 = [
    ("$ cat slides.md", GRAY),
    ("  ...(markdown content)...", GRAY),
    ("", FG),
    ("$ pandoc slides.md -t beamer \\", GREEN),
    ("    --pdf-engine=pdflatex \\", GREEN),
    ("    -o slides.pdf", GREEN),
    ("", FG),
    ("  Compiling...", YELLOW),
]
scenes.append((s2, 1800))

s2b = list(s2[:-1]) + [("  ✓ slides.pdf created (6 slides)", GREEN)]
scenes.append((s2b, 1200))

# Scene 3: Analyze
s3 = [
    ("$ python analyze_slides.py slides.pdf", GREEN),
    ("", FG),
    ("Analyzing slides.pdf: 6 slides", FG, "bold"),
    ("", FG),
    ("Slide 1: Title              ✅ (15 words)", GREEN),
    ("Slide 2: The Core Idea      ✅ (52 words)", GREEN),
    ("Slide 3: Why It Works       ✅ (36 words)", GREEN),
    ("Slide 4: Variants           ✅ (58 words)", GREEN),
    ("Slide 5: Convergence        ✅ (55 words)", GREEN),
    ("Slide 6: Summary", FG),
    ("  🟡 [TEXT_OVERLAP] 3.5px overlap", YELLOW),
    ("", FG),
    ("SUMMARY:", FG, "bold"),
    ("  Total slides: 6", FG),
    ("  Issues: 1 slide (minor overlap)", YELLOW),
]
scenes.append((s3, 2500))

# Scene 4: Fix & recompile
s4 = [
    ("$ # Fix: split long list on slide 6", GRAY),
    ("$ vim slides.md", GREEN),
    ("  ...adjusting bullet spacing...", GRAY),
    ("", FG),
    ("$ pandoc slides.md -t beamer \\", GREEN),
    ("    --pdf-engine=pdflatex -o slides.pdf", GREEN),
    ("  ✓ Recompiled", GREEN),
    ("", FG),
    ("$ python analyze_slides.py slides.pdf", GREEN),
    ("", FG),
    ("Slide 1: Title              ✅", GREEN),
    ("Slide 2: The Core Idea      ✅", GREEN),
    ("Slide 3: Why It Works       ✅", GREEN),
    ("Slide 4: Variants           ✅", GREEN),
    ("Slide 5: Convergence        ✅", GREEN),
    ("Slide 6: Summary            ✅", GREEN),
    ("", FG),
    ("  All slides clean! 🎉", GREEN, "bold"),
]
scenes.append((s4, 3000))

# Build GIF
frames = []
for lines, duration_ms in scenes:
    frame = make_frame(lines)
    # Approximate: GIF duration is in centiseconds
    # We add the frame multiple times or use duration parameter
    frames.append((frame, duration_ms))

# Save
output = os.path.join(os.path.dirname(__file__), "..", "assets", "demo.gif")
imgs = [f[0] for f in frames]
durations = [f[1] for f in frames]
imgs[0].save(output, save_all=True, append_images=imgs[1:],
             duration=durations, loop=0)
print(f"Saved {output} ({len(imgs)} frames)")
