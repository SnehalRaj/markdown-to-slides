#!/usr/bin/env python3
"""Convert PDF slides to PNG images for README showcase."""
import fitz
import sys
import os

def convert(pdf_path, output_dir, dpi=200):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        out = os.path.join(output_dir, f"slide_{i+1}.png")
        pix.save(out)
        paths.append(out)
        print(f"  Saved {out} ({pix.width}x{pix.height})")
    doc.close()
    return paths

if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "examples/showcase.pdf"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "assets/showcase"
    print(f"Converting {pdf} → {outdir}/")
    convert(pdf, outdir)
    print("Done!")
