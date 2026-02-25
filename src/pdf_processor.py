"""
PDF Processor – Read text from PDFs and redact identified entities.
Uses PyMuPDF (fitz) for all PDF operations.
"""

import fitz  # PyMuPDF
from typing import Dict, Tuple, List
import os


# Turquoise colour for redaction boxes  (R, G, B  0-1 float)
TURQUOISE = (0.0, 0.808, 0.820)
TURQUOISE_DARK = (0.0, 0.545, 0.545)


def extract_text(pdf_path: str) -> str:
    """Extract the full plain text from a PDF. Requires the PDF to have embedded text."""
    doc = fitz.open(pdf_path)
    pages_text: List[str] = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    doc.close()
    full = "\n".join(pages_text)
    if not full.strip():
        raise ValueError(
            "Das PDF enthält keinen erkennbaren Text. "
            "Bitte stellen Sie sicher, dass das PDF Texterkennung (OCR) hat."
        )
    return full


def redact_pdf(
    pdf_path: str,
    output_path: str,
    entity_map: Dict[str, Tuple[str, str]],
    progress_callback=None,
) -> str:
    """
    Create a redacted copy of *pdf_path* at *output_path*.

    For every occurrence of an entity key (from *entity_map*) the text is
    covered with a turquoise rectangle and the assigned variable label is
    placed on top.

    *entity_map*: {original_text: (variable_id, category)}

    Returns the output path.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Sort entities by length descending so longer matches are found first
    sorted_entities = sorted(entity_map.keys(), key=len, reverse=True)

    for page_idx, page in enumerate(doc):
        if progress_callback:
            progress_callback(int((page_idx / total_pages) * 100))

        for entity_text in sorted_entities:
            var_id, category = entity_map[entity_text]

            # Search for all occurrences on this page
            text_instances = page.search_for(entity_text)

            for inst in text_instances:
                # inst is a fitz.Rect – the bounding box of the found text

                # Draw filled turquoise rectangle to cover the original text
                shape = page.new_shape()
                shape.draw_rect(inst)
                shape.finish(color=TURQUOISE_DARK, fill=TURQUOISE, width=0.5)
                shape.commit()

                # Determine font size that fits in the box
                box_width = inst.width
                box_height = inst.height
                label = var_id

                # Calculate a font size that fits
                font_size = min(box_height * 0.85, 11)
                if font_size < 5:
                    font_size = 5

                # Measure text width and shrink font if needed
                test_width = fitz.get_text_length(label, fontname="helv", fontsize=font_size)
                while test_width > box_width - 2 and font_size > 4:
                    font_size -= 0.5
                    test_width = fitz.get_text_length(label, fontname="helv", fontsize=font_size)

                # Center the label inside the rectangle
                text_x = inst.x0 + (box_width - test_width) / 2
                text_y = inst.y0 + (box_height + font_size * 0.35) / 2

                # Insert the variable label in white bold text
                page.insert_text(
                    fitz.Point(text_x, text_y),
                    label,
                    fontname="helv",
                    fontsize=font_size,
                    color=(1, 1, 1),  # white text
                )

    if progress_callback:
        progress_callback(100)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path


def get_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count
