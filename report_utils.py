from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from regression_utils import compute_technical_indicators
import os

def format_rag_insight_to_bullets(rag_insight):
    styles = getSampleStyleSheet()
    bullets = []
    for line in rag_insight.split("\n"):
        line = line.strip().replace("**", "")
        if line.startswith(("*", "-")):
            bullets.append(ListItem(Paragraph(line[1:].strip(), styles["BodyText"])))
        elif line:
            bullets.append(ListItem(Paragraph(line.strip(), styles["BodyText"])))
    return bullets

def generate_pdf_report(symbol, start_date, end_date, r2_score, plot_path,
                        predicted_date=None, predicted_value=None, rag_insight=None,
                        executive_summary=None, risk_analysis=None, methodology=None,
                        output_path="outputs"):
    os.makedirs(output_path, exist_ok=True)
    filename = os.path.join(output_path, f"{symbol}_financial_report_{start_date}_to_{end_date}.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # 1. Executive Summary
    elements.append(Paragraph(f"📘 Financial Summary Report for {symbol}", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("1. Executive Summary", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    if executive_summary:
        elements.append(ListFlowable(format_rag_insight_to_bullets(executive_summary), bulletType="bullet"))
    elements.append(Spacer(1, 0.2 * inch))

    # 2. Market Analysis
    elements.append(Paragraph("2. Market Analysis", styles["Heading2"]))
    if rag_insight:
        elements.append(ListFlowable(format_rag_insight_to_bullets(rag_insight), bulletType="bullet"))
    elements.append(Spacer(1, 0.2 * inch))

    # 3. Technical Indicators
    indicators = compute_technical_indicators(symbol, start_date, end_date)
    elements.append(Paragraph("3. Technical Indicators", styles["Heading2"]))
    tech_lines = [f"R² score from regression: {r2_score:.4f}"]
    if indicators:
        if indicators.get("volatility"): tech_lines.append(f"Volatility: {indicators['volatility']:.4f}")
        if indicators.get("average_return"): tech_lines.append(f"Average daily return: {indicators['average_return']:.4f}")
        if indicators.get("max_drawdown"): tech_lines.append(f"Max drawdown: {indicators['max_drawdown']:.2%}")
        if indicators.get("ma20"): tech_lines.append(f"20-day MA: ${indicators['ma20']:.2f}")
        if indicators.get("ma50"): tech_lines.append(f"50-day MA: ${indicators['ma50']:.2f}")
    elements.append(ListFlowable(format_rag_insight_to_bullets("\n".join(tech_lines))))
    elements.append(Spacer(1, 0.2 * inch))

    # 4. Predictions
    if predicted_date and predicted_value:
        elements.append(Paragraph(f"📈 Predicted price on <b>{predicted_date}</b>: <b>${predicted_value:.2f}</b>", styles["BodyText"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("4. Price Predictions", styles["Heading2"]))
    if plot_path and os.path.exists(plot_path):
        try:
            img = Image(plot_path, width=6.0 * inch, height=3.0 * inch)
            elements.append(img)
        except:
            elements.append(Paragraph("⚠️ Could not load plot.", styles["BodyText"]))
    else:
        elements.append(Paragraph("No plot available.", styles["BodyText"]))
    elements.append(Spacer(1, 0.2 * inch))

    # 5. Risk Analysis
    elements.append(Paragraph("5. Risk Analysis", styles["Heading2"]))
    if risk_analysis:
        elements.append(ListFlowable(format_rag_insight_to_bullets(risk_analysis), bulletType="bullet"))

    # 6. Methodology
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("6. Data Sources and Methodology", styles["Heading2"]))
    default_method = (
        "• Stock price data retrieved from Alpha Vantage API\n"
        "• Financial news collected from NewsAPI\n"
        "• Company financial reports extracted and stored in PostgreSQL\n"
        "• Economic indicators retrieved from Alpha Vantage macroeconomic endpoints\n"
        "• Data stored in PostgreSQL (structured) and MongoDB (unstructured where applicable)\n"
        "• Vector embeddings generated using Gemini (text-embedding-004)\n"
        "• Semantic search implemented using FAISS vector store\n"
        "• Multi-index RAG pipeline combining price, economic, news, and report data\n"
        "• Query parameters (company symbol and date range) extracted using Gemini\n"
        "• Polynomial regression applied to stock prices using scikit-learn\n"
        "• Technical indicators calculated: volatility, moving averages, average return, max drawdown\n"
        "• AI-generated summaries (executive summary, risk analysis, methodology) created using Gemini\n"
        "• PDF reports generated with ReportLab including AI and regression analysis\n"
        "• Rate limiting, API key validation, and timeout enforcement implemented for security\n"
        "• Logging enabled for traceability and error handling\n"
        "• Dockerized setup with PostgreSQL initialization and automated indexing"
    )
    elements.append(ListFlowable(format_rag_insight_to_bullets(default_method), bulletType="bullet"))
    elements.append(Spacer(1, 0.3 * inch))

    footer = f"📌 Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(footer, styles["Normal"]))

    doc.build(elements)
    return filename
