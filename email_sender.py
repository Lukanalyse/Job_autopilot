"""
email_sender.py · Automated batch-mailer for CV + cover-letter PDFs
==================================================================
Sends application e-mails generated elsewhere.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
import os
import mimetypes
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import pandas as pd

# ---------------------------------------------------------------------------
# Project paths / constants
# ---------------------------------------------------------------------------
from .config import DATA_FILE, CV_DIR, LM_DIR

SMTP_PORT = 587  # default STARTTLS port

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read(sheet: str) -> pd.DataFrame:
    """Read a sheet from the master Excel file and replace NaN with ''. """
    return pd.read_excel(DATA_FILE, sheet_name=sheet).fillna("")


def smtp_host(address: str) -> str:
    """
    Infer an SMTP host from the sender e-mail address when the *senders*
    sheet does not provide `smtp_host`.
    """
    addr = address.lower()
    if addr.endswith("@gmail.com"):
        return "smtp.gmail.com"
    if addr.endswith(("@outlook.com", "@hotmail.com", "@live.com")):
        return "smtp-mail.outlook.com"
    # fall-back, works for most Google-Workspace domains
    return "smtp.gmail.com"


# ---------------------------------------------------------------------------
# Pick a sender account (single- or multi-account mode)
# ---------------------------------------------------------------------------
def pick_sender() -> tuple[dict, pd.DataFrame | None]:
    """
    Returns a tuple (sender_dict, senders_df_or_None).

    Multi-account:
        * Reads the *senders* sheet with columns
          [email, password, daily_limit, sent_today, smtp_host?]
        * Picks the account with the lowest `sent_today` < `daily_limit`
        * Increments `sent_today` for that row (to be written back later)

    Single-account:
        * Falls back on environment variables:
          SMTP_EMAIL / SMTP_PASSWORD [/ SMTP_HOST]
    """
    try:
        df = _read("senders")

        # Make sure numeric columns are int, NaN → 0
        df["daily_limit"] = pd.to_numeric(df["daily_limit"], errors="coerce").fillna(0).astype(int)
        df["sent_today"]  = pd.to_numeric(df["sent_today"],  errors="coerce").fillna(0).astype(int)

        avail = df[df.sent_today < df.daily_limit]
        if avail.empty:
            raise RuntimeError("No sender available – all daily quotas reached")

        # Select the one that has sent the fewest messages today
        snd = avail.sort_values("sent_today").iloc[0]
        df.loc[snd.name, "sent_today"] += 1
        return snd.to_dict(), df

    except (ValueError, FileNotFoundError):
        # Sheet *senders* missing → single-account mode
        return (
            {
                "email":    os.getenv("SMTP_EMAIL"),
                "password": os.getenv("SMTP_PASSWORD"),
                "smtp_host": os.getenv("SMTP_HOST") or smtp_host(os.getenv("SMTP_EMAIL", "")),
            },
            None,
        )


# ---------------------------------------------------------------------------
# Build an e-mail with HTML body + attachments
# ---------------------------------------------------------------------------
def build_msg(
    frm: str,
    to: str,
    sub: str,
    html: str,
    files: list[Path],
) -> EmailMessage:
    """Return a fully-formed EmailMessage (multipart/alternative + attachments)."""
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = frm, to, sub

    msg.set_content("Veuillez afficher ce message en HTML.")  # plain-text fallback
    msg.add_alternative(html, subtype="html")                 # HTML part

    for f in files:
        mime = mimetypes.guess_type(f)[0] or "application/pdf"
        maintype, subtype = mime.split("/")
        msg.add_attachment(
            f.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=f.name,
        )
    return msg


def send_email(host: str, snd: dict, msg: EmailMessage) -> None:
    """Send *msg* through STARTTLS SMTP."""
    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, SMTP_PORT) as server:
        server.starttls(context=ctx)
        server.login(snd["email"], snd["password"])
        server.send_message(msg)


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------
def send_applications(force: bool = False) -> None:
    """
    Loop over rows in *applications* where
        generate_lm == 'Y'  AND  email_sent is blank,
    then e-mail CV + cover letter, mark the row as sent.

    Parameters
    ----------
    force : bool
        If True, continue sending even after one SMTP failure.
    """
    profs  = _read("profiles")
    offers = _read("joboffers")
    apps   = _read("applications")

    # Add a timestamp column the first time we run
    if "sent_at" not in apps.columns:
        apps["sent_at"] = ""

    mask_no_email = apps.email_sent.isna() | (apps.email_sent.str.strip() == "")
    todo = apps[(apps.generate_lm.str.upper() == "Y") & mask_no_email]

    if todo.empty:
        print("Aucun e-mail à envoyer.")
        return

    senders_df: pd.DataFrame | None = None  # updated if multi-account mode

    # -----------------------------------------------------------------------
    # Iterate over applications to be sent
    # -----------------------------------------------------------------------
    for idx, row in todo.iterrows():
        profil = profs.loc[profs.profile_id == row.profile_id].squeeze()
        offer  = offers.loc[offers.job_id   == row.job_id   ].squeeze()

        # -------------------------------------------------------------------
        # Locate PDF files
        # -------------------------------------------------------------------
        cv_pdf = next(CV_DIR.glob(f"CV_{profil.nom.upper()}_{profil.prenom}.pdf"), None)
        lm_pdf = LM_DIR / f"LM_{profil.nom.upper()}_{profil.prenom}_{row.job_id}.pdf"

        if not (cv_pdf and lm_pdf.exists()):
            print("‼️  PDF manquant :", row.profile_id, row.job_id)
            continue

        # -------------------------------------------------------------------
        # Compose HTML body (very simple here)
        # -------------------------------------------------------------------
        body_html = (
            "<p>Bonjour,</p>"
            f"<p>Veuillez trouver ci-joint mon CV et ma lettre de motivation pour "
            f"le poste <strong>{getattr(offer, 'intitulé', '…')}</strong>.</p>"
            f"<p>Cordialement,<br>{profil.prenom} {profil.nom}</p>"
        )

        # Pick sender account (rotates if multi-account)
        sender, senders_df = pick_sender()
        host = sender.get("smtp_host") or smtp_host(sender["email"])

        msg = build_msg(
            frm  = sender["email"],
            to   = offer.recruiter_email,
            sub  = f"Candidature – {profil.prenom} {profil.nom}",
            html = body_html,
            files= [cv_pdf, lm_pdf],
        )

        # -------------------------------------------------------------------
        # Send and update tracking columns
        # -------------------------------------------------------------------
        try:
            send_email(host, sender, msg)
            print(f"📧  {profil.prenom} {profil.nom} → {offer.recruiter_email}  ({host})")
            apps.at[idx, "email_sent"] = "YES"
            apps.at[idx, "sent_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        except Exception as exc:
            print("‼️  Échec d’envoi :", exc)
            if not force:
                break  # stop the loop on first SMTP failure unless --force

    # -----------------------------------------------------------------------
    # Persist updated Excel sheets
    # -----------------------------------------------------------------------
    with pd.ExcelWriter(DATA_FILE, mode="a", if_sheet_exists="replace") as writer:
        apps.to_excel(writer, sheet_name="applications", index=False)
        if senders_df is not None:  # multi-account quotas updated
            senders_df.to_excel(writer, sheet_name="senders", index=False)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    send_applications()