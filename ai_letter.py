from __future__ import annotations

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
from pathlib import Path          # path manipulation (cross-platform)
import os                         # environment variables
import textwrap                   # multi-line string dedent

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
from dotenv import load_dotenv    # read .env files into the environment
import openai                     # OpenAI Python SDK

# ---------------------------------------------------------------------------
# Load OpenAI API key
#   1. Resolve project root (one level above /src)
#   2. Load the .env file located at that root
#   3. Pull OPENAI_API_KEY into the SDK
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)
openai.api_key = os.getenv("OPENAI_API_KEY")  # raises later if missing

# ---------------------------------------------------------------------------
# French HR-style system prompt
#   • Explains the expected structure (Objet + 4 paragraphs)
#   • Enforces stylistic constraints (short sentences, no extra commas)
#   • Ends with a fixed polite closing
# ---------------------------------------------------------------------------
SYS_PROMPT: str = textwrap.dedent(
    """
    Tu es un assistant RH francophone.
    Commence par une ligne Objet en gras et soulignée contenant Candidature au poste l’intitulé du poste, puis saute une ligne blanche.
    Rédige ensuite quatre paragraphes séparés par une ligne blanche.
    Ne répète jamais le nom, la ville, l’e-mail ni le téléphone (déjà présents dans l’en-tête).
    Utilise des phrases courtes ; ne mets pas de virgule avant « et ».

    Paragraphe 1 : parcours académique + accroche expliquant pourquoi ce poste motive la·le candidat·e.
    Paragraphe 2 : une ou deux expériences (stages ou projets) pour illustrer les compétences clés liées au poste.
    Paragraphe 3 : ce que la·le candidat·e apportera concrètement à l’entreprise et à l’équipe.
    Paragraphe 4 : ce que ce poste lui apportera pour développer son projet professionnel.

    Termine par la phrase :
    « Dans l’attente de votre retour, je vous prie d’agréer, Madame, Monsieur, l’expression de mes salutations distinguées. »

    N’emploie ni crochets ni placeholders.
    """
)

# ---------------------------------------------------------------------------
# generate_letter_text
# ---------------------------------------------------------------------------
def generate_letter_text(profil: dict, job_infos: str) -> str:
    """
    Generate a French cover-letter (lettre de motivation).

    Parameters
    ----------
    profil : dict
        Candidate information: keys include 'nom', 'prenom', 'ville', etc.
    job_infos : str
        Free-form description of the job posting.

    Returns
    -------
    str
        The full letter body, ready to be injected in an HTML template.
    """
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",              # GPT-4o (cost-efficient tier)
        messages=[
            {"role": "system", "content": SYS_PROMPT},  # style & structure
            {
                "role": "user",
                # Pass profile + job description to the assistant
                "content": (
                    f"PROFIL = {profil}\n\n"
                    f"DESCRIPTION = {job_infos}\n\n"
                    "Rédige la lettre."
                ),
            },
        ],
        temperature=0.7,                  # small creativity
        max_tokens=450,                   # plenty for 4 paragraphs
    )
    # Return the assistant’s reply without leading/trailing whitespace
    return resp.choices[0].message.content.strip()