import io
import json
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, RateLimitError
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ReportSection(BaseModel):
    heading: str = Field(description="Short professional section heading")
    body: str = Field(description="One concise paragraph grounded only in the supplied portfolio metrics")


class WrittenPortfolioReport(BaseModel):
    executive_summary: str
    strengths: list[str]
    watch_items: list[str]
    sections: list[ReportSection]
    closing_summary: str


class ReportGenerationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _money(value):
    sign = "-" if value < 0 else ""
    return f"{sign}INR {abs(value):,.0f}"


def _percentage(value):
    return f"{value:+.2f}%"


def _report_context(analysis):
    return {
        "portfolio_name": analysis["meta"]["portfolio_name"],
        "data_notice": analysis["meta"]["data_notice"],
        "summary": analysis["summary"],
        "performance": analysis["performance"],
        "concentration": analysis["concentration"],
        "risk_breakdown": analysis["risk_breakdown"],
        "stress_scenarios": analysis["stress_scenarios"],
        "sector_performance": analysis["sector_performance"],
        "holdings": [
            {
                "symbol": item["symbol"],
                "sector": item["sector"],
                "market_cap": item["market_cap"],
                "weight": item["weight"],
                "return_percentage": item["return_percentage"],
                "return_contribution": item["return_contribution"],
                "pnl": item["pnl"],
            }
            for item in analysis["holdings"]
        ],
    }


def build_automated_report(analysis):
    summary = analysis["summary"]
    performance = analysis["performance"]
    concentration = analysis["concentration"]
    winners_ratio = summary["winners_count"] / summary["holdings_count"] * 100
    strongest_sector = max(
        analysis["sector_performance"],
        key=lambda item: item["return_percentage"],
    )
    weakest_sector = min(
        analysis["sector_performance"],
        key=lambda item: item["return_percentage"],
    )
    highest_risk = max(analysis["risk_breakdown"], key=lambda item: item["score"])
    worst_stress = min(
        analysis["stress_scenarios"],
        key=lambda item: item["portfolio_impact_percentage"],
    )

    strengths = []
    if summary["total_return"] > 0:
        strengths.append(
            f"The portfolio is above acquisition cost by {_money(summary['total_pnl'])}, equal to {_percentage(summary['total_return'])}."
        )
    if summary["diversification_score"] >= 70:
        strengths.append(
            f"The diversification score is {summary['diversification_score']:.0f}/100 across {summary['sectors_count']} sectors."
        )
    if summary["risk_score"] < 45:
        strengths.append(
            f"The calculated portfolio risk score is contained at {summary['risk_score']:.1f}/100."
        )
    if winners_ratio >= 60:
        strengths.append(
            f"{summary['winners_count']} of {summary['holdings_count']} holdings are currently profitable."
        )
    if not strengths:
        strengths.append(
            "The portfolio has complete verified inputs that support position, sector, and stress analysis."
        )

    watch_items = []
    if concentration["level"] != "Low":
        watch_items.append(
            f"Concentration is {concentration['level'].lower()}: the top three holdings form {concentration['top_three_weight']:.1f}%."
        )
    if concentration["largest_sector_weight"] >= 35:
        watch_items.append(
            f"{concentration['largest_sector']} is the largest sector at {concentration['largest_sector_weight']:.1f}%."
        )
    if summary["losers_count"]:
        watch_items.append(
            f"{summary['losers_count']} holding(s) trade below acquisition cost, led by {performance['worst_holding']['symbol']}."
        )
    if highest_risk["level"] == "High":
        watch_items.append(
            f"The largest risk flag is {highest_risk['name'].lower()}: {highest_risk['detail']}"
        )
    if not watch_items:
        watch_items.append(
            "No major concentration warning is present, but portfolio weights and supplied prices should still be reviewed regularly."
        )

    sections = [
        {
            "heading": "Performance overview",
            "body": (
                f"Current value is {_money(summary['current_value'])} against {_money(summary['invested_value'])} invested. "
                f"Gross gains are {_money(performance['gross_gains'])} and gross losses are {_money(performance['gross_losses'])}. "
                f"{performance['best_holding']['symbol']} is the strongest holding at {_percentage(performance['best_holding']['return_percentage'])}, "
                f"while {performance['worst_holding']['symbol']} is the weakest at {_percentage(performance['worst_holding']['return_percentage'])}."
            ),
        },
        {
            "heading": "Diversification and concentration",
            "body": (
                f"The portfolio contains {summary['holdings_count']} holdings across {summary['sectors_count']} sectors, "
                f"but its effective-holdings measure is {summary['effective_holdings']:.1f}. "
                f"The largest position is {concentration['largest_holding']} at {concentration['largest_holding_weight']:.1f}%, "
                f"and the top three positions together account for {concentration['top_three_weight']:.1f}%."
            ),
        },
        {
            "heading": "Sector and risk profile",
            "body": (
                f"{strongest_sector['name']} is the strongest sector by return at {_percentage(strongest_sector['return_percentage'])}; "
                f"{weakest_sector['name']} is the weakest at {_percentage(weakest_sector['return_percentage'])}. "
                f"The overall heuristic risk score is {summary['risk_score']:.1f}/100, with {highest_risk['name'].lower()} "
                f"currently producing the largest risk indicator."
            ),
        },
        {
            "heading": "Stress-test interpretation",
            "body": (
                f"Among the preset illustrations, '{worst_stress['name']}' has the largest estimated effect at "
                f"{_percentage(worst_stress['portfolio_impact_percentage'])}, taking portfolio value to approximately "
                f"{_money(worst_stress['stressed_value'])}. These scenarios are linear sensitivity checks rather than forecasts."
            ),
        },
    ]

    return {
        "executive_summary": (
            f"{analysis['meta']['portfolio_name']} has a health score of {summary['health_score']:.0f}/100, "
            f"a {_percentage(summary['total_return'])} total return, and a {concentration['level'].lower()} concentration classification. "
            f"The portfolio is currently driven by {performance['best_holding']['symbol']}, while "
            f"{performance['worst_holding']['symbol']} deserves the closest performance review."
        ),
        "strengths": strengths[:4],
        "watch_items": watch_items[:4],
        "sections": sections,
        "closing_summary": (
            "Overall, the portfolio combines positive return drivers with identifiable concentration and downside sensitivities. "
            "Future decisions should also consider the investor's goals, time horizon, liquidity needs, and risk tolerance, none of which are inferred here."
        ),
    }


def generate_ai_report(analysis):
    if not os.getenv("OPENAI_API_KEY"):
        raise ReportGenerationError(
            "OPENAI_API_KEY is missing. Add it to backend/.env and restart Flask.",
            503,
        )

    instructions = """
You are PortfolioLens, an educational Indian equity portfolio-report writer.

Write a professional, plain-English interpretation using only the supplied verified metrics.
- Do not claim access to live market data, news, fundamentals, valuation, investor goals, or future prices.
- Do not provide buy, sell, hold, target-price, timing, or guaranteed-return recommendations.
- Do not invent causes for performance or infer facts that are absent.
- Explain both strengths and watch items with specific supplied numbers.
- Treat risk scores and stress tests as heuristic illustrations, not forecasts.
- Keep each section concise and useful to a non-expert investor.
- The closing summary must remind the reader that goals, time horizon, liquidity needs, and risk tolerance are not known.
""".strip()

    try:
        client = OpenAI()
        response = client.responses.parse(
            model=os.getenv("OPENAI_REPORT_MODEL", "gpt-5.6-luna"),
            reasoning={"effort": os.getenv("OPENAI_REPORT_REASONING_EFFORT", "low")},
            instructions=instructions,
            input=json.dumps(_report_context(analysis), separators=(",", ":")),
            text_format=WrittenPortfolioReport,
            max_output_tokens=1800,
            store=False,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ReportGenerationError("The AI could not create the portfolio report.", 422)
        return {
            "report": parsed.model_dump(),
            "model": os.getenv("OPENAI_REPORT_MODEL", "gpt-5.6-luna"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except AuthenticationError as error:
        raise ReportGenerationError("The OpenAI API key is invalid or inactive.", 401) from error
    except RateLimitError as error:
        raise ReportGenerationError(
            "The OpenAI API quota or rate limit was reached. Check API billing and try again.",
            429,
        ) from error
    except APIConnectionError as error:
        raise ReportGenerationError("Could not connect to the OpenAI API.", 502) from error
    except APIStatusError as error:
        raise ReportGenerationError(
            f"OpenAI report generation failed with status {error.status_code}.",
            502,
        ) from error
    except ReportGenerationError:
        raise
    except Exception as error:
        raise ReportGenerationError("The AI report could not be generated.", 502) from error


def _safe(value):
    return escape(str(value))


def build_report_pdf(report, summary, portfolio_name, report_label):
    output = io.BytesIO()
    page_width, page_height = A4
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
        title=f"{portfolio_name} - PortfolioLens Report",
        author="PortfolioLens",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PortfolioTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=23,
        textColor=colors.HexColor("#0B261A"),
        spaceAfter=3 * mm,
    )
    subtitle_style = ParagraphStyle(
        "PortfolioSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#567064"),
        spaceAfter=4 * mm,
    )
    heading_style = ParagraphStyle(
        "PortfolioHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0B5D3B"),
        spaceBefore=2.5 * mm,
        spaceAfter=1 * mm,
    )
    body_style = ParagraphStyle(
        "PortfolioBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#243C32"),
        spaceAfter=2 * mm,
    )
    small_style = ParagraphStyle(
        "PortfolioSmall",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#61756B"),
    )
    center_small = ParagraphStyle(
        "PortfolioCenterSmall",
        parent=small_style,
        alignment=TA_CENTER,
    )
    bullet_style = ParagraphStyle(
        "PortfolioBullet",
        parent=body_style,
        leftIndent=4 * mm,
        firstLineIndent=-3 * mm,
        bulletIndent=0,
        spaceAfter=0.8 * mm,
    )

    story = [
        Paragraph("PortfolioLens", title_style),
        Paragraph(_safe(portfolio_name), ParagraphStyle(
            "PortfolioName",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#172F25"),
            spaceAfter=1 * mm,
        )),
        Paragraph(
            f"{_safe(report_label)} | Generated {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}",
            subtitle_style,
        ),
    ]

    summary_data = [
        [
            Paragraph("<b>Current value</b>", center_small),
            Paragraph("<b>Total return</b>", center_small),
            Paragraph("<b>Health score</b>", center_small),
            Paragraph("<b>Risk score</b>", center_small),
        ],
        [
            Paragraph(_safe(_money(summary["current_value"])), center_small),
            Paragraph(_safe(_percentage(summary["total_return"])), center_small),
            Paragraph(f"{summary['health_score']:.0f}/100", center_small),
            Paragraph(f"{summary['risk_score']:.1f}/100", center_small),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[(page_width - 36 * mm) / 4] * 4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECF8F1")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B8DCC8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CDE7D8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([
        summary_table,
        Spacer(1, 3 * mm),
        Paragraph("Executive summary", heading_style),
        Paragraph(_safe(report["executive_summary"]), body_style),
    ])

    strengths = [Paragraph("<b>Strengths</b>", heading_style)]
    strengths.extend(
        Paragraph(f"- {_safe(item)}", bullet_style)
        for item in report["strengths"]
    )
    watch_items = [Paragraph("<b>Watch items</b>", heading_style)]
    watch_items.extend(
        Paragraph(f"- {_safe(item)}", bullet_style)
        for item in report["watch_items"]
    )
    two_column = Table(
        [[strengths, watch_items]],
        colWidths=[(page_width - 40 * mm) / 2] * 2,
        hAlign="LEFT",
    )
    two_column.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F1FAF5")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FFF7EA")),
        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#C8E3D4")),
        ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#E7D4B1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([two_column, Spacer(1, 2 * mm)])

    for section in report["sections"]:
        story.append(KeepTogether([
            Paragraph(_safe(section["heading"]), heading_style),
            Paragraph(_safe(section["body"]), body_style),
        ]))

    story.extend([
        Spacer(1, 1 * mm),
        Paragraph("Overall perspective", heading_style),
        Paragraph(_safe(report["closing_summary"]), body_style),
        Spacer(1, 2 * mm),
    ])

    disclaimer = Table(
        [[Paragraph(
            "<b>Important:</b> This report uses user-supplied portfolio data and educational heuristics. "
            "It is not investment advice, a recommendation, or a forecast. Prices may not be live. "
            "Verify every holding and consult a qualified professional where appropriate.",
            small_style,
        )]],
        colWidths=[page_width - 36 * mm],
    )
    disclaimer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F5F4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CDD5D1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(disclaimer)

    def draw_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D8E5DE"))
        canvas.line(18 * mm, 11.5 * mm, page_width - 18 * mm, 11.5 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#70837A"))
        canvas.drawString(18 * mm, 7.5 * mm, "PortfolioLens - Educational portfolio analytics")
        canvas.drawRightString(page_width - 18 * mm, 7.5 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    output.seek(0)
    return output.getvalue()
