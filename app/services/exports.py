import csv
from datetime import datetime

from fpdf import FPDF

from app.services.formatting import datetime_text, money


def export_cuts_csv(cuts: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["ID", "Fecha y Hora", "Total ($)", "Tickets", "Detalles"])
        for cut in cuts:
            writer.writerow(
                [
                    cut.get("id", ""),
                    datetime_text(cut.get("created_at", "")),
                    f"{float(cut.get('total') or 0):.2f}",
                    cut.get("tickets", 0),
                    cut.get("details") or "",
                ]
            )


class CutsPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(29, 53, 87)
        self.cell(0, 10, "HISTORIAL DE CORTES", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"Pagina {self.page_no()}", align="C")


def _wrap_lines(pdf: FPDF, text: str, width: float) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if pdf.get_string_width(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_row(
    pdf: FPDF,
    cells: list[str],
    widths: list[float],
    alignments: list[str],
    bold: bool = False,
    fill: bool = False,
) -> None:
    pdf.set_font("Helvetica", "B" if bold else "", 8)
    line_height = 4.6
    wrapped = [_wrap_lines(pdf, cell, width - 2) for cell, width in zip(cells, widths)]
    line_count = max(len(lines) for lines in wrapped)
    height = line_count * line_height + 1.6
    if pdf.get_y() + height > pdf.h - 15:
        pdf.add_page()
    x = pdf.get_x()
    y = pdf.get_y()
    for lines, width, alignment in zip(wrapped, widths, alignments):
        pdf.set_xy(x, y)
        pdf.multi_cell(
            width,
            line_height,
            "\n".join(lines),
            border=1,
            align=alignment,
            fill=fill,
            new_x="LEFT",
            new_y="TOP",
        )
        x += width
    pdf.set_xy(pdf.l_margin, y + height)


def export_cuts_pdf(cuts: list[dict], path: str, symbol: str = "$") -> None:
    pdf = CutsPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, f"Exportado: {datetime_text(datetime.now().isoformat())}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    widths = [14, 42, 28, 18, 88]
    alignments = ["C", "C", "R", "C", "L"]
    pdf.set_fill_color(226, 236, 247)
    _draw_row(
        pdf,
        ["ID", "Fecha y Hora", "Total ($)", "Tickets", "Detalles"],
        widths,
        alignments,
        bold=True,
        fill=True,
    )

    total = 0.0
    for cut in cuts:
        total += float(cut.get("total") or 0)
        _draw_row(
            pdf,
            [
                f"#{cut.get('id', '')}",
                datetime_text(cut.get("created_at", "")),
                f"{float(cut.get('total') or 0):.2f}",
                str(cut.get("tickets", 0)),
                cut.get("details") or "",
            ],
            widths,
            alignments,
        )

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, f"Total general: {money(total, symbol)}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)
