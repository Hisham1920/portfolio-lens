import io

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from pydantic import ValidationError
from werkzeug.utils import secure_filename

from services.portfolio_analyser import analyse_portfolio
from services.document_extractor import (
    DocumentExtractionError,
    extract_portfolio_documents,
    validate_uploads,
)
from services.report_generator import (
    ReportGenerationError,
    WrittenPortfolioReport,
    build_report_pdf,
    generate_ai_report,
)
from sample_data import DEMO_HOLDINGS


load_dotenv()


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/portfolio/demo")
def demo_portfolio():
    return jsonify(analyse_portfolio(DEMO_HOLDINGS))


@app.post("/api/portfolio/analyse")
def analyse():
    payload = request.get_json(silent=True) or {}
    holdings = payload.get("holdings")
    portfolio_name = str(payload.get("portfolio_name") or "My Portfolio").strip()

    if not isinstance(holdings, list) or not holdings:
        return jsonify({"error": "A non-empty holdings list is required."}), 400

    try:
        return jsonify(
            analyse_portfolio(
                holdings,
                portfolio_name=portfolio_name[:60],
                data_notice="Analysis uses the prices you supplied — live market data comes next.",
            )
        )
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/portfolio/extract")
def extract_portfolio():
    if request.form.get("consent") != "true":
        return jsonify({"error": "Consent is required before AI file processing."}), 400

    files = request.files.getlist("files")

    try:
        prepared_files = validate_uploads(files)
        result = extract_portfolio_documents(prepared_files)
        return jsonify(result)
    except DocumentExtractionError as error:
        return jsonify({"error": str(error)}), error.status_code


def _analyse_report_payload(payload):
    holdings = payload.get("holdings")
    portfolio_name = str(payload.get("portfolio_name") or "My Portfolio").strip()
    if not isinstance(holdings, list) or not holdings:
        raise ValueError("A non-empty holdings list is required.")
    return analyse_portfolio(
        holdings,
        portfolio_name=portfolio_name[:60],
        data_notice="Report uses the prices you supplied - not live market data.",
    )


@app.post("/api/portfolio/report/ai")
def ai_portfolio_report():
    payload = request.get_json(silent=True) or {}
    if payload.get("consent") is not True:
        return jsonify({"error": "Consent is required before AI report generation."}), 400

    try:
        analysis = _analyse_report_payload(payload)
        return jsonify(generate_ai_report(analysis))
    except ReportGenerationError as error:
        return jsonify({"error": str(error)}), error.status_code
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/portfolio/report/pdf")
def portfolio_report_pdf():
    payload = request.get_json(silent=True) or {}

    try:
        analysis = _analyse_report_payload(payload)
        report = WrittenPortfolioReport.model_validate(payload.get("report") or {}).model_dump()
        report_label = str(payload.get("report_label") or "Automated Portfolio Report")[:80]
        pdf_bytes = build_report_pdf(
            report,
            analysis["summary"],
            analysis["meta"]["portfolio_name"],
            report_label,
        )
        safe_name = secure_filename(analysis["meta"]["portfolio_name"]) or "portfolio"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{safe_name}-PortfolioLens-report.pdf",
        )
    except ValidationError:
        return jsonify({"error": "The written report is incomplete or invalid."}), 400
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "Uploads must be 25 MB or smaller in total."}), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)
