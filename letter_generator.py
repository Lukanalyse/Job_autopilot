"""
letter_generator.py · Build personalised cover-letters (PDF)

Reads the Excel workbook, asks the OpenAI API to draft a French cover-
letter, feeds the answer into a Jinja2/HTML template and turns the
result into a PDF with **wkhtmltopdf**.

Run on its own (`python -m src.letter_generator`) to force-generate all
pending letters.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import pandas as pd              # tabular I/O
import pdfkit                    # HTML → PDF bridge
from jinja2 import Environment, FileSystemLoader  # templating

# ---------------------------------------------------------------------------
# Internal dependencies
# ---------------------------------------------------------------------------
from .ai_letter import generate_letter_text  # OpenAI wrapper
from .config    import (
    DATA_FILE, DATA_DIR, TEMPL_DIR, LM_DIR, ROOT_DIR,
)

# ---------------------------------------------------------------------------
# wkhtmltopdf configuration (absolute path on macOS brew install)
# ---------------------------------------------------------------------------
WKHTML  = "/usr/local/bin/wkhtmltopdf"
PDF_CFG = pdfkit.configuration(wkhtmltopdf=WKHTML)

# ---------------------------------------------------------------------------
# Jinja2 set-up
# ---------------------------------------------------------------------------
env   = Environment(loader=FileSystemLoader(TEMPL_DIR))
tmpl  = env.get_template("lm/lm_template.html")

# Same date for every letter generated in one run
today = date.today().strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# Small helper to read a sheet as DataFrame
# ---------------------------------------------------------------------------
def _read(sheet: str) -> pd.DataFrame:
    """Read *sheet* from the master workbook and replace NaN with ''."""
    return pd.read_excel(DATA_FILE, sheet_name=sheet).fillna("")


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------
def generate_letters(force: bool = False) -> None:
    """
    Create every missing PDF cover-letter.

    Parameters
    ----------
    force : bool
        If *True* overwrite existing PDFs, otherwise skip them.
    """
    # --- load the three relevant sheets ------------------------------------
    profiles = _read("profiles")
    offers   = _read("joboffers")
    apps     = _read("applications")

    # keep rows where email_sent is NaN or '', and generate_lm == 'Y'
    mask_no_email = apps.email_sent.isna() | (apps.email_sent.str.strip() == "")
    todo = apps[(apps.generate_lm.str.upper() == "Y") & mask_no_email]

    if todo.empty:
        print("Aucune LM à générer.")
        return

    # temporary HTML file (deleted at the end)
    tmp_html: Path = DATA_DIR / "_tmp_lm.html"

    # -----------------------------------------------------------------------
    # iterate over every application that still needs a letter
    # -----------------------------------------------------------------------
    for idx, row in todo.iterrows():
        profil = profiles.loc[profiles.profile_id == row.profile_id].squeeze()
        offer  = offers.loc[offers.job_id       == row.job_id   ].squeeze()

        file_pdf = LM_DIR / f"LM_{profil.nom.upper()}_{profil.prenom}_{row.job_id}.pdf"
        if file_pdf.exists() and not force:
            print("· Lettre déjà présente →", file_pdf.name)
            continue

        # Ask the OpenAI API to draft the body of the letter
        body = generate_letter_text(profil.to_dict(), offer.infos)

        # Fill the HTML template with the profile, body, offer and date
        html = tmpl.render(
            profil = profil,
            body   = body,
            offer  = offer,
            today  = today
        )

        # Write temp HTML then convert to PDF
        tmp_html.write_text(html, encoding="utf-8")
        pdfkit.from_file(str(tmp_html), str(file_pdf), configuration=PDF_CFG)
        print("✔ Lettre :", file_pdf.relative_to(ROOT_DIR))

    # cleanup temporary file
    tmp_html.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Allow running the module directly for manual testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    generate_letters(force=True)