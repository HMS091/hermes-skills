#!/usr/bin/env python3
# MIT License. Part of the Hermes docx skill.
"""Set the East Asian (w:eastAsia) font on every defined style of .docx files.

docx_create.py styles set only the ascii/hAnsi font, so CJK text falls back
to Word's default East Asian font. Run this after creation for CJK documents.

Usage: set_eastasia_font.py <font-name> <file.docx> [more.docx ...]
"""
import sys

from docx import Document
from docx.oxml.ns import qn


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    font = sys.argv[1]
    for path in sys.argv[2:]:
        doc = Document(path)
        for style in doc.styles:
            rpr = style.element.get_or_add_rPr()
            rfonts = rpr.find(qn("w:rFonts"))
            if rfonts is None:
                rfonts = rpr.makeelement(qn("w:rFonts"), {})
                rpr.append(rfonts)
            rfonts.set(qn("w:eastAsia"), font)
        doc.save(path)
        print(f"eastAsia={font}: {path}")


if __name__ == "__main__":
    main()
