#!/usr/bin/env python3
"""Converte um resumo em Markdown para PDF (relatório executivo A4).

Uso: python gera_pdf.py entrada.md saida.pdf [--titulo "Título do cabeçalho"]
Requer: reportlab  (pip install reportlab --break-system-packages)

Suporta: # ## ### títulos, listas com - ou *, listas numeradas, **negrito**,
*itálico*, [link](url), tabelas pipe simples, linhas horizontais (---),
citações (>) e parágrafos. O suficiente para o resumo diário da reforma.
"""
import re
import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

NAVY = colors.HexColor("#0f2a4a")
GREEN = colors.HexColor("#1e9e6a")
GRAY = colors.HexColor("#5a6472")
LIGHT = colors.HexColor("#f2f4f7")

S = {
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21,
                          textColor=NAVY, spaceAfter=4 * mm),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=17,
                          textColor=NAVY, spaceBefore=5 * mm, spaceAfter=2 * mm),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11, leading=14,
                          textColor=GREEN, spaceBefore=3 * mm, spaceAfter=1.5 * mm),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                            textColor=colors.HexColor("#1d2530"), spaceAfter=1.8 * mm),
    "li": ParagraphStyle("li", fontName="Helvetica", fontSize=9.5, leading=13.5,
                          textColor=colors.HexColor("#1d2530"), leftIndent=6 * mm,
                          bulletIndent=2 * mm, spaceAfter=1.2 * mm),
    "quote": ParagraphStyle("quote", fontName="Helvetica-Oblique", fontSize=9.5,
                             leading=13.5, textColor=GRAY, leftIndent=6 * mm,
                             spaceAfter=1.8 * mm),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11,
                            textColor=colors.HexColor("#1d2530")),
    "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=8.5,
                             leading=11, textColor=colors.white),
}


def inline(text: str) -> str:
    """Markdown inline -> mini-HTML do reportlab."""
    text = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  r'<link href="\2" color="#1e6ae0"><u>\1</u></link>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.5">\1</font>', text)
    return text


def build_table(rows):
    data = []
    for i, row in enumerate(rows):
        style = S["cellh"] if i == 0 else S["cell"]
        data.append([Paragraph(inline(c.strip()), style) for c in row])
    ncols = max(len(r) for r in data)
    width = (A4[0] - 40 * mm) / ncols
    t = Table(data, colWidths=[width] * ncols, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d0da")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def md_to_flowables(md: str):
    flow, table_buf, num = [], [], 0
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        is_table = line.lstrip().startswith("|") and line.rstrip().endswith("|")
        if table_buf and not is_table:
            flow.append(build_table(table_buf))
            flow.append(Spacer(1, 2 * mm))
            table_buf = []
        if not line.strip():
            i += 1
            continue
        if is_table:
            cells = [c for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r"\s*:?-{2,}:?\s*", c) for c in cells):
                table_buf.append(cells)
        elif line.startswith("### "):
            flow.append(Paragraph(inline(line[4:]), S["h3"]))
        elif line.startswith("## "):
            flow.append(Paragraph(inline(line[3:]), S["h2"]))
            flow.append(HRFlowable(width="100%", thickness=0.8, color=GREEN,
                                   spaceAfter=2 * mm))
        elif line.startswith("# "):
            flow.append(Paragraph(inline(line[2:]), S["h1"]))
        elif re.fullmatch(r"-{3,}|\*{3,}", line.strip()):
            flow.append(HRFlowable(width="100%", thickness=0.5,
                                   color=colors.HexColor("#c9d0da"),
                                   spaceBefore=2 * mm, spaceAfter=2 * mm))
        elif re.match(r"^\s*[-*]\s+", line):
            flow.append(Paragraph(inline(re.sub(r"^\s*[-*]\s+", "", line)),
                                  S["li"], bulletText="•"))
        elif re.match(r"^\s*\d+[.)]\s+", line):
            num += 1
            flow.append(Paragraph(inline(re.sub(r"^\s*\d+[.)]\s+", "", line)),
                                  S["li"], bulletText=f"{num}."))
        elif line.startswith("> "):
            flow.append(Paragraph(inline(line[2:]), S["quote"]))
        else:
            num = 0
            flow.append(Paragraph(inline(line), S["body"]))
        i += 1
    if table_buf:
        flow.append(build_table(table_buf))
    return flow


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    titulo = "Reforma Tributária — Monitor"
    if "--titulo" in sys.argv:
        titulo = sys.argv[sys.argv.index("--titulo") + 1]
    md = open(src, encoding="utf-8").read()

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(GREEN)
        canvas.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(20 * mm, 10 * mm,
                          f"{titulo} — gerado em {date.today().strftime('%d/%m/%Y')}")
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"pág. {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(dst, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=titulo)
    doc.build(md_to_flowables(md), onFirstPage=decorate, onLaterPages=decorate)
    print(f"PDF gerado: {dst}")


if __name__ == "__main__":
    main()
