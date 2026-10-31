"""Generazione del target checkerboard per la calibrazione delle telecamere."""

from __future__ import annotations

from pathlib import Path

try:
    from reportlab.lib.colors import black, white
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    HAS_REPORTLAB = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    black = white = None  # type: ignore[assignment]
    mm = 1.0  # type: ignore[assignment]
    canvas = None  # type: ignore[assignment]
    HAS_REPORTLAB = False


class CheckerboardError(RuntimeError):
    """Target checkerboard non generabile."""


def make_checkerboard_pdf(
    path: str | Path,
    *,
    pattern_size: tuple[int, int] = (9, 6),
    square_size_mm: float = 25.0,
    landscape_page: bool = True,
    margin_mm: float = 15.0,
) -> Path:
    """Crea un PDF A4 con un checkerboard a dimensione fisica reale.

    ``pattern_size`` e' il numero di corner interni (colonne, righe); il numero
    di quadrati e' quindi ``pattern_size + 1``.
    """
    if not HAS_REPORTLAB:
        raise CheckerboardError(
            "reportlab non installato: pip install -r software/requirements.txt"
        )
    if pattern_size[0] < 2 or pattern_size[1] < 2:
        raise ValueError("pattern_size deve avere almeno 2x2 corner")
    if square_size_mm <= 0:
        raise ValueError("square_size_mm deve essere positivo")
    if margin_mm < 0:
        raise ValueError("margin_mm non puo' essere negativo")

    columns = pattern_size[0] + 1
    rows = pattern_size[1] + 1
    board_width = columns * square_size_mm
    board_height = rows * square_size_mm
    page_width, page_height = (297.0, 210.0) if landscape_page else (210.0, 297.0)

    if board_width + 2 * margin_mm > page_width:
        raise CheckerboardError(
            f"board largo {board_width:.1f} mm non entra in {page_width:.0f} mm"
        )
    if board_height + 2 * margin_mm > page_height:
        raise CheckerboardError(
            f"board alto {board_height:.1f} mm non entra in {page_height:.0f} mm"
        )

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    document = canvas.Canvas(
        str(output),
        pagesize=(page_width * mm, page_height * mm),
    )
    document.setFillColor(white)
    document.rect(0, 0, page_width * mm, page_height * mm, fill=1, stroke=0)

    x0 = (page_width - board_width) / 2.0
    y0 = (page_height - board_height) / 2.0 + 5.0

    for row in range(rows):
        for column in range(columns):
            if (row + column) % 2 == 0:
                document.setFillColor(black)
                document.rect(
                    (x0 + column * square_size_mm) * mm,
                    (y0 + (rows - 1 - row) * square_size_mm) * mm,
                    square_size_mm * mm,
                    square_size_mm * mm,
                    fill=1,
                    stroke=0,
                )

    document.setFillColor(black)
    document.setFont("Helvetica", 9)
    document.drawString(
        15 * mm,
        8 * mm,
        f"Checkerboard {pattern_size[0]}x{pattern_size[1]} corner interni, "
        f"quadrato {square_size_mm:g} mm - stampare al 100%",
    )

    bar_y = 4 * mm
    bar_x = 15 * mm
    bar_length = 100 * mm
    document.setLineWidth(0.6)
    document.line(bar_x, bar_y, bar_x + bar_length, bar_y)
    document.line(bar_x, bar_y - 1.5 * mm, bar_x, bar_y + 1.5 * mm)
    document.line(
        bar_x + bar_length,
        bar_y - 1.5 * mm,
        bar_x + bar_length,
        bar_y + 1.5 * mm,
    )
    document.setFont("Helvetica", 7)
    document.drawString(bar_x, bar_y + 2 * mm, "100 mm")

    document.showPage()
    document.save()
    return output
