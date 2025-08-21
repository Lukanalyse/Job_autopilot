"""
main.py · High-level entry point
===============================

Sequential pipeline:

1. generate_cvs()      – build/update every missing résumé (PDF)
2. generate_letters()  – ask OpenAI for the cover-letter text, render HTML,
                         convert to PDF
3. send_applications() – e-mail each application (CV + LM) and mark success
4. quick stats printed to stdout

Run `python -m src.main` from the project root.
"""

# ---------------------------------------------------------------------------
# Pipeline imports (local packages)
# ---------------------------------------------------------------------------
from src.cv_generator     import generate_cvs
from src.letter_generator import generate_letters
from src.email_sender     import send_applications
from src.offer_loader     import load_offers, load_applications


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Execute the three-step pipeline then print quick statistics.
    """

    # 1) Resume generation (skips existing PDFs unless --force)
    generate_cvs()

    # 2) Cover-letter generation (OpenAI → HTML → PDF)
    generate_letters()

    # 3) E-mail dispatch (attaches PDFs, updates Excel)
    send_applications()

    # 4) Tiny recap
    print(f"{len(load_offers())} job offers recorded")
    print(f"{len(load_applications())} applications in total")


# ---------------------------------------------------------------------------
# Allow `python main.py` execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()