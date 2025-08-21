"""
cv_generator.py · Batch-generate PDF résumés from an Excel sheet
================================================================

Reads the *profiles* worksheet, feeds each row to a Jinja-HTML
template, then converts the HTML to PDF with wkhtmltopdf.

"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
from datetime import date
from pathlib import Path
import re                            # small regex cleaner

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import pandas as pd                  # Excel → DataFrame
import pdfkit                        # HTML → PDF via wkhtmltopdf
from jinja2 import Environment, FileSystemLoader
from .ai_profile import generate_profile_summary

# ---------------------------------------------------------------------------
# Project-level paths & constants
# ---------------------------------------------------------------------------
from .config import (
    DATA_DIR, TEMPL_DIR, CV_DIR, DATA_FILE, ROOT_DIR
)

WKHTML   = "/usr/local/bin/wkhtmltopdf"        # absolute path to wkhtmltopdf
PDF_CFG  = pdfkit.configuration(wkhtmltopdf=WKHTML)

# ---------------------------------------------------------------------------
# Jinja environment & template
# ---------------------------------------------------------------------------
env          = Environment(loader=FileSystemLoader(TEMPL_DIR))
template_cv  = env.get_template("cv/cv_template.html")

today        = date.today().isoformat()        # YYYY-MM-DD

# ---------------------------------------------------------------------------
# Helper: replace NaN / None / blank-like with ""
# ---------------------------------------------------------------------------
def _clean(d: dict) -> dict:
    """Return a copy of *d* where NaN/None/blank values → empty string."""
    return {
        k: ("" if re.fullmatch(r"(nan|none|\s*)", str(v), re.I) else v)
        for k, v in d.items()
    }

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_cvs(excel_path: Path | str = DATA_FILE, force: bool = False) -> None:
    """
    Generate all missing CVs as PDFs.

    Parameters
    ----------
    excel_path : Path | str
        Workbook containing the *profiles* sheet.
    force : bool
        If True, re-generate PDFs even if they already exist.
    """
    df = pd.read_excel(excel_path, sheet_name="profiles").fillna("")
    tmp_html = DATA_DIR / "_tmp_cv.html"        # transient file for wkhtmltopdf

    for raw in df.to_dict("records"):
        profile = _clean(raw)

        # ↳ si la cellule ‘profil_pro’ est vide on la crée « à la volée »
        if not profile["profil_pro"]:
            profile["profil_pro"] = generate_profile_summary(profile)

        file_pdf = CV_DIR / f"CV_{profile['nom'].upper()}_{profile['prenom']}.pdf"

        # Skip if already present unless --force is requested
        if file_pdf.exists() and not force:
            print(f"· CV déjà présent → {file_pdf.name}")
            continue

        # Render HTML then convert to PDF
        tmp_html.write_text(template_cv.render(profile), encoding="utf-8")
        pdfkit.from_file(str(tmp_html), str(file_pdf), configuration=PDF_CFG)

        print("✔", file_pdf.relative_to(ROOT_DIR))

    # Clean up temporary HTML
    tmp_html.unlink(missing_ok=True)