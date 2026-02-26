"""
PDF Processor – Read text from PDFs and redact identified entities.
Uses PyMuPDF (fitz) for all PDF operations.

Key features:
- Uses fitz redaction annotations so the underlying text is truly removed
  (not merely covered by a shape that could be lifted).
- Sorts entities longest-first to avoid partial matches inside longer ones.
- Appends a summary page listing all variable assignments.
- Enhanced signature / handwriting detection combining five methods:
  1. Embedded image analysis (expanded size heuristics)
  2. Vector drawing clustering (detects pen-drawn signatures)
  3. Ink / freehand annotation detection
  4. PDF form signature field detection
  5. Render-based bottom-zone scan (catch-all for missed elements)
"""

import fitz  # PyMuPDF
from typing import Dict, Tuple, List
import os


# Black colour for redaction boxes  (R, G, B  0-1 float)
BLACK = (0.0, 0.0, 0.0)
DARK_GRAY = (0.25, 0.25, 0.25)
WHITE = (1, 1, 1)

# Category labels for the summary page
CATEGORY_LABELS = {
    "VORNAME": "Vorname",
    "NACHNAME": "Nachname",
    "STRASSE": "Straße",
    "HAUSNUMMER": "Hausnummer",
    "STADT": "Stadt / Ort",
    "PLZ": "Postleitzahl",
    "LAND": "Land",
    "KONTONUMMER": "Kontonummer / IBAN",
    "EMAIL": "E-Mail-Adresse",
    "TELEFON": "Telefonnummer",
    "KRYPTO_ADRESSE": "Krypto-Adresse",
    "UNTERNEHMEN": "Unternehmen",
    "GRUNDSTUECK": "Grundstück",
    "GEBURTSDATUM": "Geburtsdatum",
    "SOZIALVERSICHERUNG": "Sozialversicherungsnummer",
    "STEUERNUMMER": "Steuernummer",
    "AUSWEISNUMMER": "Ausweisnummer",
    "GELDBETRAG": "Geldbetrag / Währung",
    "UNTERSCHRIFT": "Unterschrift / Handschrift",
}


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


def _add_redaction(page, rect: fitz.Rect, label: str):
    """Add a redaction annotation that fills *rect* with black and shows *label*."""
    if not label:
        # Signature/handwriting: solid black box, no text
        page.add_redact_annot(rect, text="", fill=BLACK)
        return

    # Calculate font size that fits the box
    box_w = rect.width
    box_h = rect.height
    font_size = min(box_h * 0.82, 11)
    if font_size < 4.5:
        font_size = 4.5

    # Shrink font if the label is too wide
    text_w = fitz.get_text_length(label, fontname="helv", fontsize=font_size)
    while text_w > box_w - 2 and font_size > 4:
        font_size -= 0.5
        text_w = fitz.get_text_length(label, fontname="helv", fontsize=font_size)

    page.add_redact_annot(
        rect,
        text=label,
        fontname="helv",
        fontsize=font_size,
        align=fitz.TEXT_ALIGN_CENTER,
        fill=BLACK,
        text_color=WHITE,
    )


# ---------------------------------------------------------------------------
# Signature / Handwriting Detection (enhanced)
# ---------------------------------------------------------------------------

# Bottom fraction of each page treated as the "signature zone" where
# detection is more aggressive.
_SIG_ZONE_FRACTION = 0.40

# Maximum gap (pt) between drawing strokes to consider them one cluster.
_CLUSTER_GAP = 20

# Minimum number of vector strokes in a cluster to flag as handwriting.
_MIN_CLUSTER_STROKES = 3

# Extra padding (pt) around every detected signature element.
_REDACT_MARGIN = 15


def _expand_rect(rect: fitz.Rect, page_rect: fitz.Rect, margin: float = 15) -> fitz.Rect:
    """Expand *rect* by *margin* in all directions, clamped to page bounds."""
    return fitz.Rect(
        max(page_rect.x0, rect.x0 - margin),
        max(page_rect.y0, rect.y0 - margin),
        min(page_rect.x1, rect.x1 + margin),
        min(page_rect.y1, rect.y1 + margin),
    )


def _cluster_rects(rects: List[fitz.Rect], max_gap: float = 20):
    """Group overlapping / nearby rectangles into clusters.

    Returns a list of ``(merged_rect, member_count)`` tuples.
    """
    if not rects:
        return []

    clusters: List[List] = [[fitz.Rect(rects[0]), 1]]

    for rect in rects[1:]:
        merged = False
        for cluster in clusters:
            padded = fitz.Rect(
                cluster[0].x0 - max_gap, cluster[0].y0 - max_gap,
                cluster[0].x1 + max_gap, cluster[0].y1 + max_gap,
            )
            if padded.intersects(rect):
                cluster[0] |= rect
                cluster[1] += 1
                merged = True
                break
        if not merged:
            clusters.append([fitz.Rect(rect), 1])

    # Iteratively merge clusters that now overlap each other.
    changed = True
    while changed:
        changed = False
        new_clusters: List[List] = []
        used: set = set()
        for i, (r1, c1) in enumerate(clusters):
            if i in used:
                continue
            for j in range(i + 1, len(clusters)):
                if j in used:
                    continue
                r2, c2 = clusters[j]
                padded = fitz.Rect(
                    r1.x0 - max_gap, r1.y0 - max_gap,
                    r1.x1 + max_gap, r1.y1 + max_gap,
                )
                if padded.intersects(r2):
                    r1 |= r2
                    c1 += c2
                    used.add(j)
                    changed = True
            new_clusters.append([r1, c1])
            used.add(i)
        clusters = new_clusters

    return [(c[0], c[1]) for c in clusters]


# -- Individual detection methods ------------------------------------------

def _redact_signature_images(page):
    """Detect and redact images that look like signatures or handwriting.

    Uses wider size ranges than before and is extra aggressive in the
    signature zone (bottom of page).
    """
    page_rect = page.rect
    sig_zone_top = page_rect.height * (1 - _SIG_ZONE_FRACTION)

    try:
        images = page.get_images(full=True)
    except Exception:
        return

    for img_info in images:
        xref = img_info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            continue
        for rect in rects:
            w, h = rect.width, rect.height
            area = w * h
            in_sig_zone = rect.y0 >= sig_zone_top

            # General signature detection (anywhere on page)
            if 30 < w < 700 and 8 < h < 300 and 400 < area < 120_000:
                expanded = _expand_rect(rect, page_rect, _REDACT_MARGIN)
                page.add_redact_annot(expanded, text="", fill=BLACK)
                continue

            # In signature zone: much wider tolerance
            if in_sig_zone and w > 15 and h > 5 and area > 150:
                if w < page_rect.width * 0.9 and h < page_rect.height * 0.3:
                    expanded = _expand_rect(rect, page_rect, _REDACT_MARGIN)
                    page.add_redact_annot(expanded, text="", fill=BLACK)


def _redact_signature_drawings(page):
    """Detect clusters of vector paths that resemble handwriting.

    Hand-drawn signatures consist of many short, often curved strokes
    clustered together – very different from table borders or form lines.
    """
    try:
        drawings = page.get_drawings()
    except Exception:
        return

    if not drawings:
        return

    page_rect = page.rect
    sig_zone_top = page_rect.height * (1 - _SIG_ZONE_FRACTION)

    stroke_rects: List[fitz.Rect] = []
    for d in drawings:
        rect = fitz.Rect(d["rect"])

        # Skip page-wide horizontal rules / table borders
        if rect.width > page_rect.width * 0.7 and rect.height < 3:
            continue
        # Skip full-height elements (side borders)
        if rect.height > page_rect.height * 0.4:
            continue
        # Skip large filled backgrounds / boxes
        if rect.width * rect.height > page_rect.width * page_rect.height * 0.25:
            continue
        # Skip invisible specks
        if rect.width < 1 and rect.height < 1:
            continue

        stroke_rects.append(rect)

    if not stroke_rects:
        return

    clusters = _cluster_rects(stroke_rects, max_gap=_CLUSTER_GAP)

    for cluster_rect, stroke_count in clusters:
        in_sig_zone = cluster_rect.y0 >= sig_zone_top
        min_strokes = 2 if in_sig_zone else _MIN_CLUSTER_STROKES

        if stroke_count < min_strokes:
            continue

        # Skip overly large clusters that are probably layout elements
        if cluster_rect.width > page_rect.width * 0.7 and cluster_rect.height > 200:
            continue

        expanded = _expand_rect(cluster_rect, page_rect, _REDACT_MARGIN)
        page.add_redact_annot(expanded, text="", fill=BLACK)


def _redact_ink_annotations(page):
    """Detect and redact Ink (freehand) annotations – digital pen signatures."""
    try:
        annot = page.first_annot
    except Exception:
        return

    while annot:
        try:
            # PDF annotation type 19 = Ink (freehand drawing)
            if annot.type[0] == 19:
                expanded = _expand_rect(annot.rect, page.rect, _REDACT_MARGIN)
                page.add_redact_annot(expanded, text="", fill=BLACK)
            annot = annot.next
        except Exception:
            break


def _redact_form_signature_fields(page):
    """Detect and redact PDF form signature widgets."""
    try:
        widget = page.first_widget
    except Exception:
        return

    while widget:
        try:
            # field_type 7 = signature field in PyMuPDF
            if widget.field_type == 7:
                expanded = _expand_rect(widget.rect, page.rect, _REDACT_MARGIN)
                page.add_redact_annot(expanded, text="", fill=BLACK)
            widget = widget.next
        except Exception:
            break


def _redact_bottom_zone_scan(page):
    """Render-based catch-all: render the signature zone at low resolution
    and look for dark marks in areas that contain no text blocks.

    This catches signatures embedded as XObjects, unusual image formats,
    or any other visual element the targeted methods above may miss.
    """
    page_rect = page.rect
    sig_zone_top = page_rect.height * (1 - _SIG_ZONE_FRACTION)

    # Collect text-block rectangles inside the signature zone
    text_rects: List[fitz.Rect] = []
    try:
        for block in page.get_text("blocks"):
            r = fitz.Rect(block[:4])
            if r.y1 > sig_zone_top:
                text_rects.append(r)
    except Exception:
        pass

    # Render at low resolution (48 DPI) for speed
    scale = 48.0 / 72.0
    mat = fitz.Matrix(scale, scale)
    clip = fitz.Rect(page_rect.x0, sig_zone_top, page_rect.x1, page_rect.y1)

    try:
        pix = page.get_pixmap(matrix=mat, clip=clip, colorspace=fitz.csGRAY)
    except Exception:
        return

    pw, ph = pix.width, pix.height
    if pw < 2 or ph < 2:
        return

    samples = pix.samples  # grayscale bytes (one byte per pixel)

    # Divide the rendered zone into a grid of cells (~30 px each)
    n_cols = max(1, pw // 30)
    n_rows = max(1, ph // 30)
    cell_w = pw / n_cols
    cell_h = ph / n_rows

    suspect_cells: List[fitz.Rect] = []

    for row in range(n_rows):
        for col in range(n_cols):
            # Map cell back to page coordinates
            cell_x0 = page_rect.x0 + col * cell_w / scale
            cell_y0 = sig_zone_top + row * cell_h / scale
            cell_x1 = cell_x0 + cell_w / scale
            cell_y1 = cell_y0 + cell_h / scale
            cell_page_rect = fitz.Rect(cell_x0, cell_y0, cell_x1, cell_y1)

            # Skip cells that overlap known text blocks
            if any(cell_page_rect.intersects(tr) for tr in text_rects):
                continue

            # Count dark pixels in this cell
            px0 = int(col * cell_w)
            py0 = int(row * cell_h)
            px1 = min(int((col + 1) * cell_w), pw)
            py1 = min(int((row + 1) * cell_h), ph)

            dark = 0
            total = 0
            for y in range(py0, py1):
                offset = y * pw
                for x in range(px0, px1):
                    if samples[offset + x] < 120:
                        dark += 1
                    total += 1

            # Flag cells where > 2 % of pixels are dark (non-text marks)
            if total > 0 and dark / total > 0.02:
                suspect_cells.append(cell_page_rect)

    if not suspect_cells:
        return

    # Merge adjacent suspect cells and redact broad areas
    clusters = _cluster_rects(suspect_cells, max_gap=10)
    for merged_rect, count in clusters:
        if count >= 2:
            expanded = _expand_rect(merged_rect, page.rect, _REDACT_MARGIN)
            page.add_redact_annot(expanded, text="", fill=BLACK)


# -- Orchestrator -----------------------------------------------------------

def _detect_and_redact_signatures(page):
    """Run all signature / handwriting detection methods on *page*."""
    _redact_signature_images(page)
    _redact_signature_drawings(page)
    _redact_ink_annotations(page)
    _redact_form_signature_fields(page)
    _redact_bottom_zone_scan(page)


def redact_pdf(
    pdf_path: str,
    output_path: str,
    entity_map: Dict[str, Tuple[str, str]],
    progress_callback=None,
) -> str:
    """
    Create a redacted copy of *pdf_path* at *output_path*.

    For every occurrence of an entity key the text is permanently redacted
    (underlying text removed) and replaced with a black box showing the
    assigned variable label.

    *entity_map*: {original_text: (variable_id, category)}

    Returns the output path.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Sort entities by length descending so longer matches are processed first
    sorted_entities = sorted(entity_map.keys(), key=len, reverse=True)

    for page_idx, page in enumerate(doc):
        if progress_callback:
            progress_callback(int((page_idx / total_pages) * 100))

        for entity_text in sorted_entities:
            var_id, _category = entity_map[entity_text]

            # Search for all occurrences on this page
            text_instances = page.search_for(entity_text)

            for inst in text_instances:
                _add_redaction(page, inst, var_id)

        # Redact signatures, handwriting, ink annotations, etc.
        _detect_and_redact_signatures(page)

        # Apply all redactions for this page at once (removes underlying text)
        page.apply_redactions()

    # -- Append summary page listing all variable assignments --
    _append_summary_page(doc, entity_map)

    if progress_callback:
        progress_callback(100)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path


def _append_summary_page(doc: fitz.Document, entity_map: Dict[str, Tuple[str, str]]):
    """Append a page at the end of *doc* listing all variable -> category mappings."""
    # A4 page size
    page_w, page_h = 595.28, 841.89
    page = doc.new_page(width=page_w, height=page_h)

    margin = 50
    y = margin

    # Title
    page.insert_text(
        fitz.Point(margin, y + 20),
        "Anonymisierungs-Verzeichnis",
        fontname="helv",
        fontsize=18,
        color=DARK_GRAY,
    )
    y += 45

    # Subtitle
    page.insert_text(
        fitz.Point(margin, y + 12),
        "Zuordnung der verwendeten Variablen zu Kategorien",
        fontname="helv",
        fontsize=10,
        color=(0.4, 0.4, 0.4),
    )
    y += 30

    # Horizontal rule
    shape = page.new_shape()
    shape.draw_line(fitz.Point(margin, y), fitz.Point(page_w - margin, y))
    shape.finish(color=DARK_GRAY, width=1.5)
    shape.commit()
    y += 15

    # Table header
    col_var = margin
    col_cat = margin + 80
    col_note = margin + 240

    page.insert_text(fitz.Point(col_var, y + 10), "Variable", fontname="helv", fontsize=9, color=DARK_GRAY)
    page.insert_text(fitz.Point(col_cat, y + 10), "Kategorie", fontname="helv", fontsize=9, color=DARK_GRAY)
    page.insert_text(fitz.Point(col_note, y + 10), "Hinweis", fontname="helv", fontsize=9, color=DARK_GRAY)
    y += 20

    # Sorted by variable name
    entries = sorted(entity_map.items(), key=lambda x: x[1][0])

    for original_text, (var_id, category) in entries:
        if not var_id:
            continue  # Skip entries without variable (e.g. signatures)

        if y > page_h - margin - 20:
            # New page if we run out of space
            page = doc.new_page(width=page_w, height=page_h)
            y = margin

        cat_label = CATEGORY_LABELS.get(category, category)

        # Draw a small black chip for the variable
        var_w = fitz.get_text_length(var_id, fontname="helv", fontsize=9) + 8
        chip_rect = fitz.Rect(col_var, y, col_var + var_w, y + 14)
        shape = page.new_shape()
        shape.draw_rect(chip_rect)
        shape.finish(color=DARK_GRAY, fill=BLACK, width=0.3)
        shape.commit()
        page.insert_text(
            fitz.Point(col_var + 4, y + 10),
            var_id,
            fontname="helv",
            fontsize=9,
            color=WHITE,
        )

        # Category
        page.insert_text(
            fitz.Point(col_cat, y + 10),
            cat_label,
            fontname="helv",
            fontsize=9,
            color=(0.2, 0.2, 0.2),
        )

        # Hint: show how many characters the original had (no cleartext!)
        hint = f"{len(original_text)} Zeichen"
        page.insert_text(
            fitz.Point(col_note, y + 10),
            hint,
            fontname="helv",
            fontsize=8,
            color=(0.5, 0.5, 0.5),
        )

        y += 20

    # Footer
    y = page_h - margin
    page.insert_text(
        fitz.Point(margin, y),
        "Erstellt mit PDF Anonymizer",
        fontname="helv",
        fontsize=8,
        color=(0.6, 0.6, 0.6),
    )


def get_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count
