# ---------------------------------------------------------------------------
# config.py · Centralised project paths & .env loading
# ---------------------------------------------------------------------------
# This module exposes constant `Path` objects that other modules import
# (data directories, template folder, Excel file location, …).
# It also ensures that the `.env` file is parsed once at start-up so every
# module importing `config` has the environment variables available.
# ---------------------------------------------------------------------------

from pathlib import Path      # ↳ cross-platform filesystem paths
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Root & sub-directories
# ---------------------------------------------------------------------------
ROOT_DIR  = Path(__file__).resolve().parent.parent  # project root  …/Job_autopilot/
DATA_DIR  = ROOT_DIR / "data"                       # …/data
TEMPL_DIR = ROOT_DIR / "templates"                  # …/templates

# Main Excel workbook (profiles, offers, applications)
DATA_FILE = DATA_DIR / "profiles_job_test.xlsx"

# Output folders for generated PDFs
CV_DIR = DATA_DIR / "cv"    # Curriculum vitae PDFs
LM_DIR = DATA_DIR / "lm"    # Lettres de motivation PDFs

# Create the folders at import-time (idempotent: exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)
LM_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load .env once so every module gets the variables (OpenAI key, SMTP, …)
# ---------------------------------------------------------------------------
load_dotenv(ROOT_DIR / ".env", override=True)