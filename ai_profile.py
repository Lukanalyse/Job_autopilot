# src/ai_profile.py
from pathlib import Path
from dotenv import load_dotenv
import os, openai, textwrap

# charge la clé OpenAI définie dans .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)
openai.api_key = os.getenv("OPENAI_API_KEY")

SYS_PROMPT = textwrap.dedent("""
    Rédige, à la première personne et sur un ton neutre, un résumé professionnel d'environ 40 mots (2 ou 3 phrases). C'est pour l'entête d'un CV.
N’y fais figurer ni âge ni coordonnées.
Mets en avant mes compétences clés, ma formation, ma motivation et mon objectif de décrocher un premier CDI, en tenant compte du fait que je ne possède pour l’instant que des stages comme expériences.
Tu finiras par à la recherche d'un premier CDI dans le domaine ... 
""")

def generate_profile_summary(profil: dict) -> str:
    r = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.6,
        max_tokens=120,
        messages=[
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user",
             "content": f"Voici le profil :\n{profil}\n\nÉcris le résumé."}
        ],
    )
    return r.choices[0].message.content.strip()