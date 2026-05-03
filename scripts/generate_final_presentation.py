#!/usr/bin/env python3
"""Generate the final IEDA4920 FYP presentation deck.

The deck is designed for a 20-minute academic review presentation.  It follows
the reference deck's finance-oriented style cues: serif typography, dark navy
and muted gold accents, assertive thesis titles, image-led evidence slides, and
compact bottom takeaways.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "IEDA4920_Final_Presentation.pptx"
COVER_BG = ROOT / "report" / "figures" / "final_deck_cover_background.png"

SLIDE_W = 13.333
SLIDE_H = 7.5

INK = RGBColor(14, 41, 65)
INK_DARK = RGBColor(6, 23, 38)
INK_MID = RGBColor(47, 73, 95)
GOLD = RGBColor(147, 134, 0)
GOLD_LIGHT = RGBColor(222, 212, 142)
RED = RGBColor(192, 0, 0)
TEAL = RGBColor(32, 128, 130)
PAPER = RGBColor(248, 248, 246)
PAPER_2 = RGBColor(242, 244, 245)
LINE_GREY = RGBColor(205, 211, 214)
MID_GREY = RGBColor(116, 119, 122)
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(255, 255, 255)

TITLE_FONT = "Times New Roman"
BODY_FONT = "Times New Roman"


def set_background(slide, color: RGBColor = PAPER) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _fit_font_size(text: str, base_size: int, width_in: float, height_in: float) -> int:
    """Conservative heuristic to keep long labels inside native text boxes."""
    if not text:
        return base_size
    line_count = max(1, text.count("\n") + 1)
    max_chars = max(len(line) for line in text.split("\n"))
    char_budget = max(16, int(width_in * 9.2))
    line_budget = max(1, int(height_in * 2.2))
    size = base_size
    if max_chars > char_budget:
        size -= int((max_chars - char_budget) / 8) + 1
    if line_count > line_budget:
        size -= int((line_count - line_budget) * 2)
    return max(9, min(base_size, size))


def add_text(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    size: int = 18,
    color: RGBColor = BLACK,
    bold: bool = False,
    italic: bool = False,
    align: PP_ALIGN | None = None,
    font: str = BODY_FONT,
    fit: bool = True,
    valign: MSO_ANCHOR | None = None,
):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE if fit else None
    tf.margin_left = Inches(0.03)
    tf.margin_right = Inches(0.03)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    if valign is not None:
        tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    if align is not None:
        p.alignment = align
    p.space_after = Pt(0)
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(_fit_font_size(text, size, w, h) if fit else size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    return shape


def add_rule(slide, x: float, y: float, w: float, h: float, color: RGBColor = INK):
    shp = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    return shp


def add_panel(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: RGBColor = WHITE,
    line: RGBColor | None = LINE_GREY,
    width: float = 1.0,
    radius: bool = False,
):
    shp = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(w),
        Inches(h),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(width)
    return shp


def set_shape_text(
    shape,
    text: str,
    size: int = 16,
    color: RGBColor = BLACK,
    bold: bool = False,
    align: PP_ALIGN = PP_ALIGN.CENTER,
    font: str = BODY_FONT,
):
    shape.text_frame.clear()
    shape.text_frame.word_wrap = True
    shape.text_frame.margin_left = Inches(0.06)
    shape.text_frame.margin_right = Inches(0.06)
    shape.text_frame.margin_top = Inches(0.03)
    shape.text_frame.margin_bottom = Inches(0.03)
    shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = shape.text_frame.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(_fit_font_size(text, size, shape.width / Inches(1), shape.height / Inches(1)))
    run.font.color.rgb = color
    run.font.bold = bold
    return shape


def add_label(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: RGBColor = WHITE,
    line: RGBColor | None = LINE_GREY,
    size: int = 15,
    color: RGBColor = INK,
    bold: bool = False,
    radius: bool = False,
):
    shp = add_panel(slide, x, y, w, h, fill=fill, line=line, radius=radius)
    return set_shape_text(shp, text, size=size, color=color, bold=bold)


def add_arrow(slide, x: float, y: float, w: float, h: float, color: RGBColor = INK):
    arrow = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = color
    arrow.line.fill.background()
    return arrow


def add_header(slide, title: str, subtitle: str, slide_no: int, section: str) -> None:
    add_text(slide, title, 0.32, 0.25, 8.9, 0.42, size=22, color=INK, bold=True)
    add_text(slide, subtitle, 0.32, 0.75, 9.6, 0.34, size=15, color=MID_GREY)
    add_text(slide, section.upper(), 10.65, 0.32, 1.65, 0.28, size=10, color=GOLD, bold=True, align=PP_ALIGN.RIGHT)
    add_text(slide, f"{slide_no:02d}", 12.45, 0.27, 0.42, 0.28, size=11, color=MID_GREY, align=PP_ALIGN.RIGHT)
    add_rule(slide, 0.32, 1.16, 12.35, 0.02, INK)
    add_rule(slide, 0.32, 1.19, 3.2, 0.035, GOLD)


def add_takeaway(slide, text: str, label: str = "Takeaway") -> None:
    add_rule(slide, 0.64, 6.58, 11.98, 0.025, LINE_GREY)
    add_text(slide, label, 0.74, 6.77, 1.2, 0.26, size=11, color=GOLD, bold=True)
    add_text(slide, text, 1.82, 6.70, 10.55, 0.38, size=15, color=INK, bold=True)


def add_bullets(
    slide,
    items: Iterable[str],
    x: float,
    y: float,
    w: float,
    h: float,
    size: int = 18,
    color: RGBColor = BLACK,
    accent: RGBColor = GOLD,
    gap: float = 0.47,
) -> None:
    yy = y
    for idx, item in enumerate(items, start=1):
        add_rule(slide, x, yy + 0.08, 0.08, 0.08, accent)
        add_text(slide, item, x + 0.22, yy - 0.02, w - 0.22, 0.38, size=size, color=color)
        yy += gap
        if yy > y + h:
            break


def add_numbered_points(
    slide,
    points: Sequence[tuple[str, str]],
    x: float,
    y: float,
    w: float,
    step: float,
    size: int = 17,
):
    for i, (head, body) in enumerate(points, start=1):
        yy = y + (i - 1) * step
        add_text(slide, f"{i}", x, yy, 0.36, 0.38, size=22, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, head, x + 0.55, yy - 0.02, w - 0.55, 0.28, size=size, color=INK, bold=True)
        add_text(slide, body, x + 0.55, yy + 0.32, w - 0.55, 0.42, size=size - 3, color=MID_GREY)


def add_image_fit(slide, path: Path, x: float, y: float, w: float, h: float, border: bool = True):
    if not path.exists():
        add_panel(slide, x, y, w, h, fill=PAPER_2, line=LINE_GREY)
        add_text(slide, f"Figure unavailable: {path.name}", x + 0.25, y + h / 2 - 0.18, w - 0.5, 0.35, size=14, color=MID_GREY, align=PP_ALIGN.CENTER)
        return None
    if border:
        add_panel(slide, x - 0.05, y - 0.05, w + 0.1, h + 0.1, fill=WHITE, line=LINE_GREY)
    with Image.open(path) as img:
        iw, ih = img.size
    box_ratio = w / h
    img_ratio = iw / ih
    if img_ratio > box_ratio:
        new_w = w
        new_h = w / img_ratio
        new_x = x
        new_y = y + (h - new_h) / 2
    else:
        new_h = h
        new_w = h * img_ratio
        new_x = x + (w - new_w) / 2
        new_y = y
    return slide.shapes.add_picture(str(path), Inches(new_x), Inches(new_y), Inches(new_w), Inches(new_h))


def add_metric(slide, value: str, label: str, x: float, y: float, w: float, color: RGBColor = INK) -> None:
    add_text(slide, value, x, y, w, 0.45, size=27, color=color, bold=True)
    add_text(slide, label, x, y + 0.48, w, 0.32, size=12, color=MID_GREY)


def add_metric_stack(slide, metrics: Sequence[tuple[str, str]], x: float, y: float, w: float, step: float = 1.05) -> None:
    for i, (label, value) in enumerate(metrics):
        add_metric(slide, value, label, x, y + i * step, w, color=INK if i == 0 else TEAL)


def add_mini_table(slide, rows: Sequence[Sequence[str]], x: float, y: float, col_ws: Sequence[float], row_h: float = 0.42) -> None:
    total_w = sum(col_ws)
    add_rule(slide, x, y, total_w, 0.035, INK)
    for r, row in enumerate(rows):
        yy = y + 0.08 + r * row_h
        if r == 0:
            add_rule(slide, x, yy + row_h - 0.05, total_w, 0.015, LINE_GREY)
        xx = x
        for c, text in enumerate(row):
            color = INK if r == 0 else BLACK
            bold = r == 0
            add_text(slide, text, xx + 0.04, yy, col_ws[c] - 0.08, row_h - 0.05, size=12 if r == 0 else 13, color=color, bold=bold)
            xx += col_ws[c]


def read_outputs():
    macro = pd.read_csv(ROOT / "outputs/gat/GAT_output_macro/goodness_of_fit_metrics_macro_OOS.csv")
    meso = pd.read_csv(ROOT / "outputs/gat/GAT_output_meso/goodness_of_fit_metrics_meso_OOS.csv")
    robust = pd.read_csv(ROOT / "outputs/gat/robust_oos_evaluation.csv")
    port = pd.read_csv(ROOT / "outputs/portfolio/GAT_portfolio_output/portfolio_performance_summary_ranked.csv")
    spread = pd.read_csv(ROOT / "outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv")
    spread_hac = pd.read_csv(ROOT / "outputs/portfolio/GAT_portfolio_output/top_bottom_spread_robust_inference.csv")
    dav = pd.read_csv(ROOT / "outputs/econometrics/dav_peak_analysis/dav_peak_summary.csv")
    return macro, meso, robust, port, spread, spread_hac, dav


def metric(df: pd.DataFrame, target: str, model: str, col: str) -> float:
    row = df[(df["Target"] == target) & (df["Model"] == model)].iloc[0]
    return float(row[col])


def make_cover_background() -> None:
    returns_path = ROOT / "outputs/portfolio/GAT_portfolio_output/returns_GAT_LongShort_TopBottomQuintile_return_only.csv"
    COVER_BG.parent.mkdir(parents=True, exist_ok=True)
    if not returns_path.exists():
        return
    series = pd.read_csv(returns_path, index_col=0).iloc[:, 0].astype(float)
    equity = (1 + series).cumprod()
    x = np.linspace(0, 1, len(equity))
    y = (equity - equity.min()) / max(equity.max() - equity.min(), 1e-9)
    y = 0.10 + 0.50 * y

    fig = plt.figure(figsize=(16, 9), facecolor="#061726")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#061726")
    ax.plot(x, y, color="#d8c66f", lw=4, alpha=0.95)
    ax.fill_between(x, y, 0.08, color="#d8c66f", alpha=0.08)
    bar_height = np.clip(series.values * 2, -0.08, 0.08)
    ax.bar(x, bar_height, width=0.012, bottom=0.08, color="#55a3a3", alpha=0.15)
    ax.grid(color="white", alpha=0.06, linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Dark overlay for title legibility.
    overlay = fig.add_axes([0, 0, 1, 1], facecolor="none")
    overlay.imshow(np.zeros((2, 2)), extent=[0, 1, 0, 1], cmap="gray", alpha=0.0)
    overlay.axis("off")
    fig.savefig(COVER_BG, dpi=180, bbox_inches="tight", pad_inches=0, facecolor="#061726")
    plt.close(fig)


def new_deck() -> tuple[Presentation, object]:
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    return prs, prs.slide_layouts[6]


def new_content_slide(prs: Presentation, blank, title: str, subtitle: str, n: int, section: str):
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, title, subtitle, n, section)
    return slide


def make_deck() -> None:
    macro, meso, robust, port, spread, spread_hac, dav = read_outputs()
    make_cover_background()
    prs, blank = new_deck()

    # 1. Cover
    slide = prs.slides.add_slide(blank)
    set_background(slide, INK_DARK)
    add_image_fit(slide, COVER_BG, 0, 0, SLIDE_W, SLIDE_H, border=False)
    add_panel(slide, 0.58, 1.28, 12.16, 1.65, fill=WHITE, line=INK, width=1.0)
    add_text(slide, "AI-Driven Data Research in Quantitative Finance", 1.0, 1.72, 11.35, 0.45, size=28, color=BLACK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "SEC Item 1A risk disclosures -> semantic peer graphs -> ST-GAT forecasts", 1.6, 3.42, 10.2, 0.36, size=18, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "Final Year Project Review Submission", 4.45, 4.14, 4.5, 0.32, size=18, color=GOLD_LIGHT, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "CHAN Ho Lam Myles | CHOI Man Hou | TSOI Ching Yi", 3.35, 5.58, 6.6, 0.35, size=15, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "IEDA4920 | HKUST | WorldQuant Consulting (Beijing) Co., Ltd.", 3.15, 6.18, 7.1, 0.28, size=12, color=GOLD_LIGHT, align=PP_ALIGN.CENTER)
    add_text(slide, "01", 12.42, 6.95, 0.42, 0.26, size=11, color=WHITE, align=PP_ALIGN.RIGHT)

    # 2. Thesis
    slide = new_content_slide(
        prs,
        blank,
        "The thesis: risk text is most useful when treated as topology",
        "The project converts annual disclosures into a clean graph-learning experiment.",
        2,
        "motivation",
    )
    add_text(slide, "One empirical story", 0.72, 1.62, 2.8, 0.28, size=16, color=GOLD, bold=True)
    add_text(slide, "The best tested Meso taxonomy improves OOS forecasting relative to a strict identity baseline.", 0.72, 2.0, 6.0, 1.05, size=29, color=INK, bold=True)
    add_numbered_points(
        slide,
        [
            ("Risk disclosures define peers", "Item 1A paragraphs become macro/meso exposure vectors."),
            ("Peers define topology", "Cosine similarity creates annual semantic risk graphs."),
            ("Topology is tested directly", "A_t = I removes every off-diagonal peer edge."),
        ],
        7.25,
        1.75,
        5.1,
        1.15,
        size=17,
    )
    add_takeaway(slide, "The main contribution is not another text score; it is a leakage-safe topology test.")

    # 3. Research problem
    slide = new_content_slide(
        prs,
        blank,
        "The problem is alignment: text, time, graph, and target must agree",
        "A finance project fails if the data panel is elegant but mistimed.",
        3,
        "motivation",
    )
    xs = [0.8, 3.05, 5.3, 7.55, 9.8]
    labels = ["Item 1A\ntext", "Risk\ntaxonomy", "Firm-year\nvectors", "Peer\ngraph", "Forward\ntargets"]
    for i, (x, label) in enumerate(zip(xs, labels)):
        add_label(slide, label, x, 2.1, 1.55, 0.84, fill=WHITE, line=INK, size=15, bold=True)
        if i < len(xs) - 1:
            add_arrow(slide, x + 1.66, 2.39, 0.54, 0.22, GOLD)
    add_numbered_points(
        slide,
        [
            ("Availability", "Use only information observable before the target window."),
            ("Comparability", "Keep train, validation, and OOS periods chronological."),
            ("Ablation clarity", "Hold financial features fixed and change only graph topology."),
        ],
        1.15,
        3.65,
        10.8,
        0.82,
        size=17,
    )
    add_takeaway(slide, "The experiment is designed around timing discipline before model complexity.")

    # 4. Research questions
    slide = new_content_slide(
        prs,
        blank,
        "Three questions organize the report and presentation",
        "Each question has a direct artifact and a direct validation test.",
        4,
        "motivation",
    )
    rows = [
        ("RQ1", "Can Item 1A text be mapped into stable macro-meso risk vectors?", "taxonomy and exposure matrices"),
        ("RQ2", "Does semantic risk topology improve return and volatility forecasts?", "full graph vs. identity baseline"),
        ("RQ3", "Do forecasts carry economically meaningful ranking information?", "monthly quintile backtest"),
    ]
    for i, (tag, question, artifact) in enumerate(rows):
        y = 1.72 + i * 1.35
        add_text(slide, tag, 0.88, y + 0.05, 0.7, 0.34, size=22, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, question, 1.8, y, 7.0, 0.42, size=19, color=INK, bold=True)
        add_text(slide, artifact, 9.05, y + 0.03, 3.1, 0.36, size=14, color=MID_GREY)
        add_rule(slide, 1.8, y + 0.58, 10.3, 0.012, LINE_GREY)
    add_takeaway(slide, "The deck follows the same chain: construct the panel, test the topology, then test ranking value.")

    # 5. Pipeline
    slide = new_content_slide(
        prs,
        blank,
        "The workflow is one pipeline, not disconnected experiments",
        "Every downstream result inherits timing and taxonomy choices from the text pipeline.",
        5,
        "method",
    )
    pipeline = [
        ("Extract", "SEC Item 1A\nrisk paragraphs"),
        ("Structure", "dynamic macro/\nmeso taxonomy"),
        ("Score", "firm-year\nexposure vectors"),
        ("Connect", "semantic peer\nrisk graph"),
        ("Forecast", "topology-only\nST-GAT"),
        ("Validate", "econometrics +\nportfolio tests"),
    ]
    for i, (head, body) in enumerate(pipeline):
        x = 0.55 + i * 2.08
        add_text(slide, head, x, 1.78, 1.55, 0.28, size=14, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_label(slide, body, x, 2.2, 1.55, 0.9, fill=WHITE, line=INK if i in [3, 4] else LINE_GREY, size=13, bold=i in [3, 4])
        add_text(slide, f"{i + 1}", x + 0.5, 3.32, 0.48, 0.34, size=18, color=INK, bold=True, align=PP_ALIGN.CENTER)
        if i < len(pipeline) - 1:
            add_arrow(slide, x + 1.65, 2.52, 0.48, 0.2, GOLD)
    add_text(slide, "Core design choice", 1.1, 4.62, 2.2, 0.3, size=15, color=GOLD, bold=True)
    add_text(slide, "Risk similarity defines edges; the GAT learns attention weights from topology and financial node features.", 1.1, 5.03, 10.8, 0.52, size=22, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_takeaway(slide, "The report's result tables are interpretable because each stage has an explicit input and output.")

    # 6. Data sources
    slide = new_content_slide(
        prs,
        blank,
        "The data pipeline combines disclosures, market data, and validation artifacts",
        "Section 3 of the report is the bridge from raw filings to the ST-GAT panel.",
        6,
        "data pipeline",
    )
    sources = [
        ("SEC EDGAR", "10-K filing histories and Item 1A Risk Factors text"),
        ("Daily market data", "adjusted prices, volume, benchmark prices, and SPY returns"),
        ("Macro proxies", "S&P 500, VIX, and 10-year Treasury yield features"),
        ("Output artifacts", "forecast, portfolio, DAV, FMB, and network validation files"),
    ]
    for i, (head, body) in enumerate(sources):
        x = 0.75 + (i % 2) * 6.1
        y = 1.75 + (i // 2) * 1.65
        add_text(slide, head, x, y, 2.5, 0.3, size=19, color=INK, bold=True)
        add_rule(slide, x, y + 0.44, 4.85, 0.035, GOLD if i % 2 == 0 else TEAL)
        add_text(slide, body, x, y + 0.68, 4.9, 0.45, size=16, color=MID_GREY)
    add_mini_table(
        slide,
        [
            ("Canonical artifact", "Role"),
            ("all_risk_factors_master.csv", "paragraph-level Item 1A corpus"),
            ("risk_scores_macro/meso_annual.csv", "firm-year textual risk exposures"),
            ("fin_data_matrix_enhanced.csv", "financial features and forward targets"),
        ],
        1.15,
        5.15,
        [4.3, 6.5],
        row_h=0.42,
    )
    add_takeaway(slide, "The data story starts with source traceability before moving to modeling results.")

    # 7. SEC extraction process
    slide = new_content_slide(
        prs,
        blank,
        "SEC Item 1A extraction turns raw 10-K HTML into paragraph-level risk text",
        "The report describes a four-stage extraction process before any LLM scoring is applied.",
        7,
        "data pipeline",
    )
    sec_steps = [
        ("Acquire", "download 10-K HTML\nfrom EDGAR"),
        ("Isolate", "extract Item 1A\nRisk Factors"),
        ("Structure", "separate headings\nand descriptions"),
        ("Export", "write company CSVs\nand master corpus"),
    ]
    for i, (head, body) in enumerate(sec_steps):
        x = 0.82 + i * 3.02
        add_text(slide, f"Stage {i + 1}", x, 1.72, 1.7, 0.25, size=12, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_label(slide, head, x, 2.12, 1.9, 0.58, fill=WHITE, line=INK, size=16, bold=True)
        add_text(slide, body, x, 2.92, 2.05, 0.62, size=14, color=MID_GREY, align=PP_ALIGN.CENTER)
        if i < len(sec_steps) - 1:
            add_arrow(slide, x + 2.1, 2.32, 0.48, 0.2, GOLD)
    add_bullets(
        slide,
        [
            "Boundary detection removes table-of-contents references and stops at the next filing item.",
            "Formatting heuristics identify risk headings, subheadings, and paragraph descriptions.",
            "The master CSV is the auditable text corpus used by taxonomy and classification scripts.",
        ],
        1.05,
        4.38,
        10.8,
        1.25,
        size=18,
    )
    add_takeaway(slide, "The NLP model never sees an arbitrary full 10-K; it sees a cleaned Item 1A corpus.")

    # 8. Text-to-risk scoring pipeline
    slide = new_content_slide(
        prs,
        blank,
        "Risk scoring converts paragraph labels into normalized firm-year exposures",
        "This is the quantitative representation consumed by the graph construction step.",
        8,
        "data pipeline",
    )
    scoring = [
        ("Paragraph corpus", "Company, year, heading,\nparagraph text"),
        ("Taxonomy classifier", "macro and meso\nrisk labels"),
        ("Firm-year aggregation", "category counts per\nfirm-year"),
        ("Exposure vector", "positive rows sum\nto one"),
    ]
    for i, (head, body) in enumerate(scoring):
        x = 0.65 + i * 3.05
        add_text(slide, head, x, 1.82, 2.35, 0.32, size=16, color=INK, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x, 2.32, 2.35, 0.64, size=14, color=MID_GREY, align=PP_ALIGN.CENTER)
        add_rule(slide, x + 0.36, 3.2, 1.62, 0.04, GOLD if i < 3 else TEAL)
        if i < len(scoring) - 1:
            add_arrow(slide, x + 2.48, 2.42, 0.38, 0.18, GOLD)
    add_metric(slide, "20", "macro exposure columns", 1.35, 4.35, 3.0)
    add_metric(slide, "105", "meso exposure columns", 4.98, 4.35, 3.0, TEAL)
    add_metric(slide, "2,387", "risk-score firm-year rows", 8.55, 4.35, 3.2, TEAL)
    add_takeaway(slide, "The graph is built from normalized risk exposure vectors, not raw legal text.")

    # 9. Financial feature and target matrix
    slide = new_content_slide(
        prs,
        blank,
        "Financial features and forward targets share the same July-to-June clock",
        "This alignment is the main timing safeguard in the supervised forecasting problem.",
        9,
        "data pipeline",
    )
    add_mini_table(
        slide,
        [
            ("Feature family", "Implemented fields"),
            ("Firm-specific", "Vol, Downside_Vol, MA_200_Ratio, Momentum_11M, Dollar_Volume, Log_Dollar_Volume"),
            ("Market/macro", "SP500_Ret, SP500_Vol, VIX_Avg, VIX_Change, TenY_Yield_Avg, TenY_Yield_Change"),
            ("Targets", "Target_Ret and Target_Vol over the next July-to-June window"),
        ],
        0.75,
        1.65,
        [2.35, 9.55],
        row_h=0.58,
    )
    add_panel(slide, 0.95, 4.68, 10.9, 0.18, fill=LINE_GREY, line=None)
    timing = [
        ("features + graph", "July t -> June t+1", 1.05, 4.35, INK),
        ("forward target", "July t+1 -> June t+2", 5.2, 5.35, TEAL),
    ]
    for label, years, x, w, color in timing:
        add_panel(slide, x, 4.52, w, 0.54, fill=WHITE, line=color, width=1.4)
        add_text(slide, label, x + 0.14, 4.63, 1.85, 0.24, size=13, color=color, bold=True)
        add_text(slide, years, x + w - 2.55, 4.63, 2.38, 0.24, size=13, color=INK, align=PP_ALIGN.RIGHT)
    add_takeaway(slide, "The target is strictly forward-looking: risk year t predicts the following July-to-June return and volatility.")

    # 10. Sample, splits, and timing
    slide = new_content_slide(
        prs,
        blank,
        "Sample construction is timed around annual disclosure availability",
        "The forecasting panel uses a July-to-June alignment for realized outcomes.",
        10,
        "data pipeline",
    )
    add_metric(slide, "2,387", "risk-score firm-years", 0.86, 1.72, 2.2)
    add_metric(slide, "485", "tickers in risk matrices", 3.45, 1.72, 2.2, TEAL)
    add_metric(slide, "2,367", "financial feature/target rows", 6.05, 1.72, 2.65, TEAL)
    add_panel(slide, 0.9, 3.22, 10.95, 0.18, fill=LINE_GREY, line=None)
    periods = [("Train", "2006-2016", 0.9, 4.15, INK), ("Validation", "2017-2020", 5.05, 2.8, TEAL), ("OOS review", "2021-2024", 7.95, 3.9, GOLD)]
    for label, years, x, w, color in periods:
        add_panel(slide, x, 3.05, w, 0.54, fill=WHITE, line=color, width=1.4)
        add_text(slide, label, x + 0.16, 3.16, 1.3, 0.24, size=13, color=color, bold=True)
        add_text(slide, years, x + w - 1.12, 3.16, 0.96, 0.24, size=13, color=INK, align=PP_ALIGN.RIGHT)
    add_bullets(
        slide,
        [
            "Standardization and imputation use training-year statistics.",
            "Model selection uses validation years only.",
            "Review-submission OOS results use the current exported 2021-2024 panel.",
        ],
        1.05,
        4.35,
        10.9,
        1.35,
        size=18,
    )
    add_takeaway(slide, "The key anti-leakage controls are chronological splits, train-only transforms, and forward targets.")

    # 11. Taxonomy
    slide = new_content_slide(
        prs,
        blank,
        "Macro explains broad exposure; meso gives the graph usable resolution",
        "The strongest forecasting evidence comes from the granular meso topology.",
        11,
        "method",
    )
    add_text(slide, "Macro layer", 0.88, 1.85, 2.4, 0.34, size=19, color=INK, bold=True)
    add_text(slide, "broad risk families", 0.9, 2.26, 2.7, 0.3, size=14, color=MID_GREY)
    add_text(slide, "Meso layer", 4.15, 1.85, 2.4, 0.34, size=19, color=INK, bold=True)
    add_text(slide, "specific vulnerabilities", 4.17, 2.26, 2.9, 0.3, size=14, color=MID_GREY)
    add_text(slide, "Firm-year vector", 7.72, 1.85, 2.8, 0.34, size=19, color=INK, bold=True)
    add_text(slide, "normalized exposure weights", 7.74, 2.26, 3.2, 0.3, size=14, color=MID_GREY)
    add_arrow(slide, 3.22, 2.05, 0.62, 0.23, GOLD)
    add_arrow(slide, 6.97, 2.05, 0.62, 0.23, GOLD)
    add_mini_table(
        slide,
        [
            ("Layer", "Role", "Forecast implication"),
            ("Macro", "Interpretability", "dense graph, broad similarities"),
            ("Meso", "Discrimination", "sparse graph, cleaner peer links"),
        ],
        1.05,
        3.45,
        [1.55, 4.0, 5.5],
        row_h=0.52,
    )
    add_takeaway(slide, "The meso layer is not cosmetic; it changes the graph density and signal-to-noise tradeoff.")

    # 12. Taxonomy evolution
    slide = new_content_slide(
        prs,
        blank,
        "Taxonomy evolution is kept as a method claim, not a headline result",
        "Coverage percentages are deferred until their source table and rerun script are regenerated.",
        12,
        "method",
    )
    add_image_fit(slide, ROOT / "outputs/figures/taxonomy_coverage_improvement.png", 0.78, 1.5, 5.25, 3.9)
    add_numbered_points(
        slide,
        [
            ("Detect deviations", "Embed new paragraphs and compare them with existing meso centroids."),
            ("Cluster emerging themes", "Group low-similarity paragraphs into candidate risk concepts."),
            ("Update taxonomy", "Use ADD, MERGE, or REORGANIZE decisions before rescoring."),
        ],
        6.55,
        1.72,
        5.55,
        1.13,
        size=17,
    )
    add_takeaway(slide, "The final review report separates the evolution mechanism from unsupported percentage claims.")

    # 13. Risk vectors to graph
    slide = new_content_slide(
        prs,
        blank,
        "Risk exposure vectors become annual semantic peer networks",
        "The graph is binary and topology-only: edges define peer availability, not edge weights.",
        13,
        "method",
    )
    add_text(slide, "R_i,t", 0.95, 2.05, 0.75, 0.38, size=25, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "firm-year risk vector", 0.62, 2.55, 1.45, 0.28, size=12, color=MID_GREY, align=PP_ALIGN.CENTER)
    add_arrow(slide, 2.0, 2.17, 0.62, 0.22, GOLD)
    add_label(slide, "cosine similarity\nbetween firms", 2.75, 1.85, 2.15, 0.78, fill=WHITE, line=INK, size=14, bold=True)
    add_arrow(slide, 5.1, 2.17, 0.62, 0.22, GOLD)
    add_label(slide, "threshold by year\nand layer", 5.88, 1.85, 2.1, 0.78, fill=WHITE, line=INK, size=14, bold=True)
    add_arrow(slide, 8.18, 2.17, 0.62, 0.22, GOLD)
    add_label(slide, "A_t = I + A_risk,t", 9.05, 1.88, 2.55, 0.68, fill=INK, line=None, size=17, color=WHITE, bold=True)
    add_bullets(
        slide,
        [
            "Self-loops are always included.",
            "Off-diagonal edges are generated only from risk exposure similarity.",
            "Identity baseline keeps only self-loops and removes textual peer information.",
        ],
        1.15,
        3.75,
        10.6,
        1.4,
        size=18,
    )
    add_takeaway(slide, "The graph tests whether disclosure-implied peers help after own-firm features are already present.")

    # 14. ST-GAT architecture
    slide = new_content_slide(
        prs,
        blank,
        "Topology-only ST-GAT learns from peer structure and temporal history",
        "Spatial attention is applied over annual risk-peer graphs, then forecasted through time.",
        14,
        "method",
    )
    arch = [
        ("financial\nnode features", "X_t"),
        ("risk graph\nsnapshot", "A_t"),
        ("GATConv\nspatial encoder", "H_t"),
        ("temporal\nforecaster", "H_1:T"),
        ("return + vol\nheads", "y_hat"),
    ]
    for i, (label, tag) in enumerate(arch):
        x = 0.72 + i * 2.45
        add_text(slide, tag, x + 0.38, 1.72, 0.75, 0.28, size=16, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_label(slide, label, x, 2.15, 1.75, 0.88, fill=WHITE if i != 2 else PAPER_2, line=INK if i == 2 else LINE_GREY, size=14, bold=True)
        if i < len(arch) - 1:
            add_arrow(slide, x + 1.84, 2.47, 0.45, 0.18, GOLD)
    add_mini_table(
        slide,
        [
            ("Design element", "Purpose"),
            ("Masked multi-task Huber loss", "joint return and volatility training"),
            ("Chronological graph snapshots", "no random cross-sectional split"),
            ("Validation-only Optuna tuning", "model selection before OOS review period"),
        ],
        1.15,
        3.75,
        [3.55, 7.4],
        row_h=0.48,
    )
    add_takeaway(slide, "The model is advanced, but the experiment remains interpretable because the ablation is simple.")

    # 15. Identity baseline
    slide = new_content_slide(
        prs,
        blank,
        "The identity baseline is the cleanest spatial ablation",
        "Only off-diagonal peer edges change between the full graph and the baseline.",
        15,
        "experiment",
    )
    add_text(slide, "Full graph", 1.2, 1.85, 2.6, 0.34, size=22, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "A_t = I + A_risk,t", 1.2, 2.38, 2.6, 0.34, size=17, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_rule(slide, 2.52, 3.15, 0.12, 1.6, TEAL)
    add_rule(slide, 1.7, 3.95, 1.75, 0.12, TEAL)
    add_text(slide, "risk-peer edges active", 1.0, 4.95, 3.0, 0.28, size=14, color=MID_GREY, align=PP_ALIGN.CENTER)
    add_arrow(slide, 4.72, 3.35, 1.1, 0.24, GOLD)
    add_text(slide, "remove off-diagonal edges", 4.42, 3.75, 1.75, 0.36, size=13, color=MID_GREY, align=PP_ALIGN.CENTER)
    add_text(slide, "Identity", 7.05, 1.85, 2.6, 0.34, size=22, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "A_t = I", 7.05, 2.38, 2.6, 0.34, size=17, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_rule(slide, 8.35, 3.15, 0.12, 1.6, INK)
    add_text(slide, "self-loops only", 6.82, 4.95, 3.0, 0.28, size=14, color=MID_GREY, align=PP_ALIGN.CENTER)
    add_numbered_points(
        slide,
        [
            ("Same feature panel", "The comparison does not swap in a different feature set."),
            ("Same model family", "The comparison does not rely on a weaker baseline architecture."),
            ("Different topology", "Forecast gains can be attributed to semantic peer links."),
        ],
        10.25,
        1.8,
        2.35,
        1.22,
        size=14,
    )
    add_takeaway(slide, "This baseline makes the central topology claim defensible.")

    # 16. Experimental design
    slide = new_content_slide(
        prs,
        blank,
        "The model-selection path stops before OOS evaluation",
        "Hyperparameters are chosen on validation years, then evaluated on the review panel.",
        16,
        "experiment",
    )
    add_mini_table(
        slide,
        [
            ("Stage", "Years", "What happens"),
            ("Train", "2006-2016", "fit model, scaling, imputation statistics"),
            ("Validation", "2017-2020", "Optuna selection and early stopping signal"),
            ("OOS review", "2021-2024", "reported forecast and portfolio diagnostics"),
        ],
        0.85,
        1.72,
        [2.0, 2.25, 7.3],
        row_h=0.6,
    )
    add_bullets(
        slide,
        [
            "No random split is used for the main reported forecasting experiment.",
            "Forward return and volatility targets are constructed after the feature year.",
            "Portfolio formation uses model signals before realized holding-period returns.",
        ],
        1.05,
        4.55,
        10.5,
        1.2,
        size=18,
    )
    add_takeaway(slide, "The review-submission results are OOS relative to the tuning period.")

    # 17. Macro vs meso design
    slide = new_content_slide(
        prs,
        blank,
        "Macro and meso graphs test a resolution tradeoff",
        "Broad categories increase coverage; granular categories reduce noisy peer links.",
        17,
        "experiment",
    )
    add_text(slide, "Macro graph", 1.0, 1.8, 3.0, 0.34, size=22, color=INK, bold=True)
    add_text(slide, "3,900-4,460 OOS edges/year\nabout 5.1%-5.5% density", 1.0, 2.35, 4.1, 0.68, size=18, color=MID_GREY)
    add_text(slide, "Meso graph", 7.1, 1.8, 3.0, 0.34, size=22, color=INK, bold=True)
    add_text(slide, "38-118 OOS edges/year\nbelow 0.14% active-node density", 7.1, 2.35, 4.5, 0.68, size=18, color=MID_GREY)
    add_rule(slide, 5.96, 1.65, 0.03, 3.6, LINE_GREY)
    add_text(slide, "Broad similarity", 1.0, 4.2, 2.5, 0.28, size=15, color=GOLD, bold=True)
    add_text(slide, "high connectivity, weaker discrimination", 1.0, 4.62, 4.4, 0.3, size=15, color=INK)
    add_text(slide, "Specific similarity", 7.1, 4.2, 2.6, 0.28, size=15, color=GOLD, bold=True)
    add_text(slide, "sparse connectivity, cleaner peer selection", 7.1, 4.62, 4.6, 0.3, size=15, color=INK)
    add_takeaway(slide, "The meso graph is sparse enough that improvements are not just dense smoothing.")

    # 18. Forecasting results
    slide = new_content_slide(
        prs,
        blank,
        "The theta040 Meso ST-GAT improves the core OOS forecasting metrics",
        "The strongest verified model specification is the meso full graph.",
        18,
        "results",
    )
    add_image_fit(slide, ROOT / "report/figures/oos_metric_comparison.png", 0.6, 1.48, 7.2, 4.86)
    add_metric_stack(
        slide,
        [
            ("averaged RMSE", f"{metric(meso, 'Averaged (Ret & Vol)', 'Identity Baseline', 'RMSE'):.4f} -> {metric(meso, 'Averaged (Ret & Vol)', 'ST-GAT', 'RMSE'):.4f}"),
            ("averaged MAE", f"{metric(meso, 'Averaged (Ret & Vol)', 'Identity Baseline', 'MAE'):.4f} -> {metric(meso, 'Averaged (Ret & Vol)', 'ST-GAT', 'MAE'):.4f}"),
            ("averaged Spearman", f"{metric(meso, 'Averaged (Ret & Vol)', 'Identity Baseline', 'Spearman_Rank'):.4f} -> {metric(meso, 'Averaged (Ret & Vol)', 'ST-GAT', 'Spearman_Rank'):.4f}"),
        ],
        8.32,
        1.78,
        4.1,
    )
    add_takeaway(slide, "The headline result is a verified OOS comparison against the identity baseline.")

    # 19. Volatility deep dive
    slide = new_content_slide(
        prs,
        blank,
        "The clearest forecasting gain is in volatility",
        "Risk disclosures naturally align with realized risk outcomes more than point-return forecasts.",
        19,
        "results",
    )
    add_metric(slide, "0.2240 -> 0.1565", "volatility RMSE, identity to meso ST-GAT", 0.95, 1.75, 4.4)
    add_metric(slide, "-0.1351 -> 0.1770", "volatility Spearman rank correlation", 0.95, 3.05, 4.4, TEAL)
    add_metric(slide, "topology-only", "edge information enters as peer structure", 0.95, 4.35, 4.4, GOLD)
    add_mini_table(
        slide,
        [
            ("Interpretation", "Evidence strength"),
            ("Volatility forecast", "strongest verified improvement"),
            ("Return forecast", "ranking signal is suggestive but noisier"),
            ("Portfolio evidence", "economic extension, not trading claim"),
        ],
        6.3,
        1.85,
        [3.2, 2.6],
        row_h=0.58,
    )
    add_takeaway(slide, "The report should emphasize risk forecasting and ranking separability, not causal trading language.")

    # 20. Graph density diagnostics
    slide = new_content_slide(
        prs,
        blank,
        "Graph density explains why meso topology is more informative",
        "Sparse meso links concentrate attention on high-confidence textual peers.",
        20,
        "results",
    )
    add_image_fit(slide, ROOT / "report/figures/graph_density_macro_meso.png", 0.72, 1.45, 7.05, 4.9)
    add_numbered_points(
        slide,
        [
            ("Macro", "Dense enough to blur many broad risk-family similarities."),
            ("Meso", "Sparse enough to behave like a peer-selection mechanism."),
            ("Forecast impact", "Resolution improves the quality of the graph, not only its size."),
        ],
        8.28,
        1.95,
        4.25,
        1.15,
        size=17,
    )
    add_takeaway(slide, "The graph-density diagnostic supports the report's macro-versus-meso interpretation.")

    # 21. Portfolio setup
    slide = new_content_slide(
        prs,
        blank,
        "Portfolio tests translate annual forecasts into monthly ranking diagnostics",
        "This is an academic validation layer, not a live-trading recommendation.",
        21,
        "portfolio",
    )
    flow = [
        ("Annual ST-GAT forecast", "forward return and volatility"),
        ("Score firms", "return-only, return-over-vol, composite"),
        ("Form quintiles", "top, bottom, and long-short"),
        ("Rebalance monthly", "10 bps cost + 5 bps slippage"),
    ]
    for i, (head, body) in enumerate(flow):
        x = 0.75 + i * 3.02
        add_text(slide, head, x, 1.9, 2.45, 0.3, size=16, color=INK, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x, 2.38, 2.45, 0.5, size=14, color=MID_GREY, align=PP_ALIGN.CENTER)
        add_rule(slide, x + 0.42, 3.12, 1.6, 0.04, GOLD if i == 0 else INK)
        if i < len(flow) - 1:
            add_arrow(slide, x + 2.54, 2.42, 0.34, 0.17, GOLD)
    add_bullets(
        slide,
        [
            "Signal timing follows the annual forecast and realized holding-period month.",
            "Top-minus-bottom spreads diagnose cross-sectional ranking value.",
            "Transaction costs are included before final performance metrics.",
        ],
        1.05,
        4.25,
        10.6,
        1.15,
        size=18,
    )
    add_takeaway(slide, "The backtest is useful because it checks whether forecast rankings survive portfolio formation.")

    # 22. Portfolio equity curves
    slide = new_content_slide(
        prs,
        blank,
        "The best ST-GAT ranking portfolio is economically suggestive",
        "Performance is reported as validation evidence, with short-sample caveats.",
        22,
        "portfolio",
    )
    add_image_fit(slide, ROOT / "outputs/portfolio/GAT_portfolio_output/portfolio_equity_curves.png", 0.65, 1.48, 7.25, 4.85)
    best = port.iloc[0]
    add_metric_stack(
        slide,
        [
            ("best strategy", str(best["Strategy"]).replace("_", " ")),
            ("annualized return", f"{best['Annualized_Return'] * 100:.2f}%"),
            ("Sharpe ratio", f"{best['Sharpe']:.2f}"),
            ("max drawdown", f"{best['Max_Drawdown'] * 100:.2f}%"),
        ],
        8.35,
        1.7,
        4.0,
        step=0.95,
    )
    add_takeaway(slide, "Portfolio evidence supports ranking value but is not presented as deployable alpha.")

    # 23. Spread diagnostic
    slide = new_content_slide(
        prs,
        blank,
        "Top-minus-bottom spreads test whether the ranking separates winners from losers",
        "The return-only ST-GAT signal has the strongest spread result in the current outputs.",
        23,
        "portfolio",
    )
    add_image_fit(slide, ROOT / "report/figures/portfolio_top_bottom_spread.png", 0.72, 1.45, 6.75, 4.85)
    row = spread[(spread["Model"] == "ST-GAT") & (spread["Score_Method"] == "return_only")].iloc[0]
    hac = spread_hac[(spread_hac["Model"] == "ST-GAT") & (spread_hac["Score_Method"] == "return_only")].iloc[0]
    add_metric_stack(
        slide,
        [
            ("annualized top-minus-bottom", f"{row['Annualized_TopMinusBottom'] * 100:.2f}%"),
            ("simple t-stat / p-value", f"{row['Spread_TStat']:.2f} / {row['Spread_PValue']:.3f}"),
            ("HAC t-stat / q-value", f"{hac['HAC_TStat']:.2f} / {hac['HAC_QValue_BH']:.3f}"),
        ],
        8.05,
        1.85,
        4.35,
    )
    add_text(slide, "Interpretation remains conservative: short sample, multiple comparisons, and academic backtest design.", 8.05, 5.25, 4.35, 0.5, size=15, color=MID_GREY)
    add_takeaway(slide, "The spread test is a useful economic diagnostic, not proof of live-trading profitability.")

    # 24. DAV diagnostics
    slide = new_content_slide(
        prs,
        blank,
        "Econometric appendices are treated conservatively",
        "New DAV peak files add useful diagnostics but do not overturn the main ST-GAT evidence.",
        24,
        "validation",
    )
    dav_positive = int((dav["improvement_pct"] > 0).sum())
    dav_negative = int((dav["improvement_pct"] < 0).sum())
    dav_mean = float(dav["improvement_pct"].mean())
    add_metric(slide, str(len(dav)), "DAV peak figures parsed", 0.95, 1.75, 3.5)
    add_metric(slide, f"{dav_positive} / {dav_negative}", "positive / negative peak improvements", 0.95, 3.0, 3.5, TEAL)
    add_metric(slide, f"{dav_mean:.2f}%", "mean peak-improvement diagnostic", 0.95, 4.25, 3.5, RED)
    add_numbered_points(
        slide,
        [
            ("Use as a diagnostic", "DAV peak outputs describe a robustness experiment."),
            ("Avoid headline overclaiming", "The distribution is mixed and should not be framed as broad outperformance."),
            ("Keep appendix language precise", "FMB, SAR, and DAV BIC tables remain deferred when source tables are missing."),
        ],
        5.55,
        1.8,
        6.55,
        1.2,
        size=17,
    )
    add_takeaway(slide, "The report now separates verified main results from appendix material needing complete regeneration.")

    # 25. Findings
    slide = new_content_slide(
        prs,
        blank,
        "The final findings are narrower and stronger",
        "The presentation foregrounds claims supported by current outputs.",
        25,
        "validation",
    )
    findings = [
        ("1", "Meso ST-GAT is the strongest verified forecasting specification."),
        ("2", "Granular risk topology creates sparse, high-confidence semantic peer links."),
        ("3", "The identity baseline makes the spatial ablation clean."),
        ("4", "Volatility forecasting evidence is stronger than return point forecasting."),
        ("5", "Portfolio results are economically suggestive but interpreted as academic validation."),
    ]
    for i, (num, text) in enumerate(findings):
        y = 1.62 + i * 0.88
        add_text(slide, num, 1.0, y, 0.38, 0.32, size=20, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, text, 1.65, y - 0.01, 10.4, 0.34, size=19, color=INK, bold=i == 0)
        add_rule(slide, 1.65, y + 0.48, 10.2, 0.012, LINE_GREY)
    add_takeaway(slide, "The strongest story is precise, reproducible, and modest about inference.")

    # 26. Limitations
    slide = new_content_slide(
        prs,
        blank,
        "Limitations are explicit rather than hidden in appendix claims",
        "Unsupported numerical claims are framed as future validation work.",
        26,
        "validation",
    )
    add_mini_table(
        slide,
        [
            ("Area", "Current treatment"),
            ("Taxonomy coverage percentages", "deferred until source table and rerun script are present"),
            ("LVS dynamic taxonomy case study", "event-aligned vector and nearest-peer artifact"),
            ("Fama-MacBeth and SAR tables", "methodology extensions unless regenerated"),
            ("DAV BIC benchmark", "deferred; DAV peak diagnostics are mixed"),
            ("Portfolio evidence", "academic ranking validation, not investment advice"),
        ],
        0.78,
        1.7,
        [3.3, 8.25],
        row_h=0.55,
    )
    add_takeaway(slide, "This slide is intentionally reviewer-facing: it shows research integrity, not weakness.")

    # 27. Reproducibility
    slide = new_content_slide(
        prs,
        blank,
        "The final package is organized for supervisor review and GitHub upload",
        "Validation commands, manifests, and documentation are part of the deliverable.",
        27,
        "submission",
    )
    add_text(slide, "Run from repository root", 0.95, 1.7, 3.6, 0.3, size=16, color=GOLD, bold=True)
    add_panel(slide, 0.95, 2.12, 11.25, 1.08, fill=WHITE, line=INK)
    add_text(slide, "PYTHON=.venv/bin/python bash scripts/run_pipeline.sh validate\nPYTHON=.venv/bin/python bash scripts/run_pipeline.sh github-check", 1.22, 2.37, 10.8, 0.48, size=16, color=BLACK)
    add_metric(slide, "35 passed", "validation tests", 1.05, 4.05, 2.6)
    add_metric(slide, "passed", "GitHub preflight", 4.1, 4.05, 2.6, TEAL)
    add_metric(slide, "compiled", "final PDF report", 7.0, 4.05, 2.6, TEAL)
    add_metric(slide, "editable", "PowerPoint deck", 9.75, 4.05, 2.6, GOLD)
    add_takeaway(slide, "The repository is ready for review submission with remaining limitations documented.")

    # 28. Q&A
    slide = prs.slides.add_slide(blank)
    set_background(slide, INK_DARK)
    add_rule(slide, 0.72, 1.28, 11.9, 0.02, GOLD)
    add_text(slide, "Q&A", 0.95, 2.18, 11.4, 0.8, size=54, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Discussion: taxonomy design, identity ablation, OOS evidence, and portfolio interpretation", 2.25, 3.32, 8.8, 0.34, size=18, color=GOLD_LIGHT, align=PP_ALIGN.CENTER)
    add_text(slide, "AI-Driven Data Research in Quantitative Finance", 3.1, 6.42, 7.1, 0.28, size=14, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "28", 12.42, 6.95, 0.42, 0.26, size=11, color=WHITE, align=PP_ALIGN.RIGHT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    make_deck()
