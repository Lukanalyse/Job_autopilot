"""
offer_loader.py · Tiny I/O helper for Excel sheets
==================================================

Functions
---------
_load(sheet)        : internal helper, read + fillna("")
load_offers()       : return *joboffers* worksheet
load_applications() : return *applications* worksheet

"""

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import pandas as pd  # Excel → DataFrame

# ---------------------------------------------------------------------------
# Project-level paths
# ---------------------------------------------------------------------------
from .config import DATA_FILE, DATA_DIR, ROOT_DIR


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------
def _read(sheet: str) -> pd.DataFrame:
    """
    Read *sheet* from the master Excel file and replace NaN with ''.

    Parameters
    ----------
    sheet : str
        Name of the worksheet to load.

    Returns
    -------
    pandas.DataFrame
    """
    return pd.read_excel(DATA_FILE, sheet_name=sheet).fillna("")


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------
def load_offers() -> pd.DataFrame:
    """Shortcut: return the *joboffers* worksheet."""
    return _read("joboffers")


def load_applications() -> pd.DataFrame:
    """Shortcut: return the *applications* worksheet."""
    return _read("applications")


# ---------------------------------------------------------------------------
# Quick manual test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Print a small preview when the module is executed directly
    print(load_offers().head())
    print(load_applications().head())