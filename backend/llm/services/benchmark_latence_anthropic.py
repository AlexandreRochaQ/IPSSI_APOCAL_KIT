"""
Benchmark de latence + qualité pour la génération de quiz via l'API Claude
(Anthropic) — perturbation J2.

Pendant : compare PLUSIEURS modèles Claude sur le MÊME cours de référence, avec
la MÊME machine (ici : l'API cloud d'Anthropic, donc la "machine" est identique
pour tous les modèles → comparaison équitable). Mesure : latence p50 / p95,
qualité (JSON quiz valide), tokens, coût estimé.

Pourquoi un fichier jumeau de benchmark_latence_ollama.py ?
    Le projet appelle TOUS ses fournisseurs LLM en HTTP brut via `requests`
    (cf. backend/llm/services/anthropic_client.py et la note pédagogique :
    « brancher un autre fournisseur = adapter le transport HTTP »). Pour
    benchmarker ce que le projet fait RÉELLEMENT en production, on reproduit
    exactement la même requête (mêmes en-têtes, même max_tokens, même prompt),
    plutôt que de passer par le SDK `anthropic` (dépendance que le projet
    n'utilise pas).

Usage :
    export ANTHROPIC_API_KEY=sk-ant-...
    python benchmark_latence_anthropic.py

Prérequis :
    pip install requests --break-system-packages
    Une clé API Anthropic valide (https://console.anthropic.com/).

⚠️  Ce benchmark APPELLE une API PAYANTE. Avec les réglages par défaut
    (3 modèles × 5 appels), le coût total reste de l'ordre de quelques centimes,
    mais il n'est pas nul. Le total estimé est affiché à la fin.
"""

import os
import time
import statistics
import json

import requests

# --- Paramètres du protocole de benchmark (à citer dans l'ADR) ---
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
NB_APPELS = 5  # 5 runs × 3 modèles × même cours = protocole reproductible (cf. exemple J2)
MAX_TOKENS = 4096  # identique à anthropic_client.py (obligatoire chez Anthropic)
TEMPERATURE = 0.4  # température réelle du projet (cf. doc 02-llm-integration.md)
TIMEOUT = 120  # secondes par appel

# Les 3 modèles comparés.
#   - "temperature" : Anthropic REJETTE (HTTP 400) le paramètre temperature sur
#     Opus 4.8 / 4.7 / Fable 5. On ne l'envoie donc QUE pour les modèles qui
#     l'acceptent (Haiku 4.5, Sonnet 4.6). C'est un piège concret de la bascule
#     de modèle, à documenter dans l'ADR.
#   - "prix" : tarif officiel input/output en $ par million de tokens, sert à
#     l'estimation de coût (colonne « coût » du tableau récapitulatif).
MODELES = [
    {
        "id": "claude-haiku-4-5",
        "label": "Claude Haiku 4.5",
        "temperature": True,
        "prix_in": 1.00,
        "prix_out": 5.00,
    },
    {
        "id": "claude-sonnet-4-6",
        "label": "Claude Sonnet 4.6",
        "temperature": True,
        "prix_in": 3.00,
        "prix_out": 15.00,
    },
    {
        "id": "claude-opus-4-8",
        "label": "Claude Opus 4.8",
        "temperature": False,  # temperature interdite → 400 si envoyée
        "prix_in": 5.00,
        "prix_out": 25.00,
    },
]

# Vrai prompt système du projet, copié depuis backend/llm/services/quiz_prompt.py
# (mutualisé entre tous les clients LLM : Ollama, OpenAI, Claude...)
SYSTEM_PROMPT = """Tu es un assistant pédagogique francophone spécialisé en
génération de QCM. À partir du cours fourni, tu génères exactement 10 questions
à choix multiples pour aider un étudiant à réviser.

Règles ABSOLUES :
- Exactement 10 questions.
- Chaque question a EXACTEMENT 4 options.
- Une seule bonne réponse par question, indiquée par "correct_index" (0 à 3).
- Pas de markdown, pas de balises HTML, pas d'explications hors JSON.
- Sortie = JSON STRICT et UNIQUEMENT JSON.

Format de sortie :
{
  "questions": [
    {"prompt": "...", "options": ["...","...","...","..."], "correct_index": 0},
    ... (10 entrées)
  ]
}
"""

MAX_SOURCE_CHARS = 8000  # même limite que le projet (cf. quiz_prompt.py)

# Même cours de référence que le benchmark Ollama → comparaison équitable.
TITRE_COURS = "STMG – Management, Sciences de Gestion et Numérique"
COURS_EXEMPLE = """Chapitre : La prise de décision dans les organisations
                   Introduction

                   Toute organisation, qu'il s'agisse d'une entreprise, d'une association ou d'une administration publique, doit prendre des décisions pour atteindre ses objectifs. La prise de décision est un processus essentiel qui permet d'orienter les actions et d'assurer le bon fonctionnement de l'organisation. Les décisions peuvent avoir des conséquences importantes sur les performances, la stratégie et la pérennité de l'organisation.

                   I. Qu'est-ce qu'une décision ?

                   Une décision correspond au choix effectué entre plusieurs solutions possibles afin de résoudre un problème ou d'atteindre un objectif. La décision est prise par un acteur, appelé décideur, qui peut être un dirigeant, un responsable ou un groupe de personnes.

                   Les décisions reposent généralement sur :

                   des informations disponibles ;
                   des objectifs à atteindre ;
                   des contraintes (temps, budget, réglementation, ressources humaines) ;
                   l'environnement interne et externe de l'organisation.
                   II. Les différents types de décisions

                   On distingue généralement trois catégories de décisions :

                   1. Les décisions stratégiques

                   Les décisions stratégiques concernent l'avenir à long terme de l'organisation. Elles sont prises par les dirigeants et engagent des ressources importantes.

                   Exemples :

                   lancer un nouveau produit ;
                   s'implanter dans un nouveau pays ;
                   acquérir une autre entreprise.
                   2. Les décisions tactiques

                   Les décisions tactiques, aussi appelées décisions de gestion, permettent de mettre en œuvre la stratégie définie par les dirigeants. Elles concernent le moyen terme.

                   Exemples :

                   recruter de nouveaux salariés ;
                   lancer une campagne publicitaire ;
                   organiser la production.
                   3. Les décisions opérationnelles

                   Les décisions opérationnelles concernent le fonctionnement quotidien de l'organisation. Elles sont généralement prises par les responsables opérationnels.

                   Exemples :

                   planifier les horaires ;
                   commander des fournitures ;
                   gérer les stocks.
                   III. Le processus de prise de décision

                   La prise de décision suit généralement plusieurs étapes :

                   Identifier le problème ou l'objectif.
                   Rechercher et collecter les informations nécessaires.
                   Identifier les différentes solutions possibles.
                   Évaluer les avantages et les inconvénients de chaque solution.
                   Choisir la solution la plus adaptée.
                   Mettre en œuvre la décision.
                   Contrôler les résultats obtenus.

                   Ce processus permet de limiter les risques et d'améliorer l'efficacité des décisions prises.

                   IV. Les facteurs influençant la décision

                   Plusieurs éléments peuvent influencer la prise de décision :

                   les ressources financières disponibles ;
                   les compétences des collaborateurs ;
                   la concurrence ;
                   les évolutions technologiques ;
                   les contraintes juridiques ;
                   l'environnement économique et social.

                   Les décideurs doivent également faire face à des situations d'incertitude, dans lesquelles toutes les informations ne sont pas disponibles.

                   À retenir
                   Une décision est un choix effectué pour atteindre un objectif ou résoudre un problème.
                   Il existe des décisions stratégiques, tactiques et opérationnelles.
                   La prise de décision suit un processus structuré.
                   Les décisions sont influencées par l'environnement interne et externe de l'organisation.
                   Une bonne décision repose sur des informations fiables et une analyse rigoureuse."""


def build_user_prompt(source_text: str, title: str) -> str:
    """Reproduit exactement build_user_prompt() de quiz_prompt.py."""
    truncated = source_text[:MAX_SOURCE_CHARS]
    return (
        f"TITRE DU COURS : {title}\n\n" f"COURS :\n{truncated}\n\n" f"GÉNÈRE LE JSON MAINTENANT :"
    )


USER_PROMPT = build_user_prompt(COURS_EXEMPLE, TITRE_COURS)


def percentile(donnees: list[float], p: float) -> float:
    """Calcule le percentile p (entre 0 et 100) d'une liste de valeurs."""
    donnees_triees = sorted(donnees)
    k = (len(donnees_triees) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(donnees_triees) - 1)
    if f == c:
        return donnees_triees[f]
    return donnees_triees[f] + (donnees_triees[c] - donnees_triees[f]) * (k - f)


def quiz_valide(texte: str) -> bool:
    """Vérifie que la réponse est bien un quiz JSON exploitable par le projet :
    10 questions, chacune avec 4 options et un correct_index dans [0, 3].
    C'est notre proxy objectif de qualité (en plus de la note subjective /5)."""
    try:
        data = json.loads(texte)
    except (json.JSONDecodeError, TypeError):
        return False
    questions = data.get("questions")
    if not isinstance(questions, list) or len(questions) != 10:
        return False
    for q in questions:
        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4:
            return False
        if not isinstance(q.get("correct_index"), int) or not 0 <= q["correct_index"] <= 3:
            return False
    return True


def appel_anthropic(api_key: str, modele: dict) -> tuple[float, bool, int, int]:
    """Fait un appel à l'API Claude pour un modèle donné.

    Retourne (latence_s, quiz_valide, tokens_in, tokens_out).
    """
    payload = {
        "model": modele["id"],
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": USER_PROMPT}],
    }
    # temperature uniquement pour les modèles qui l'acceptent (sinon HTTP 400)
    if modele["temperature"]:
        payload["temperature"] = TEMPERATURE

    debut = time.perf_counter()
    response = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    fin = time.perf_counter()

    data = response.json()
    texte = data["content"][0]["text"]
    usage = data.get("usage", {})
    return (
        fin - debut,
        quiz_valide(texte),
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
    )


def cout_estime(modele: dict, tokens_in: int, tokens_out: int) -> float:
    """Coût en dollars pour les tokens consommés par ce modèle."""
    return (tokens_in / 1_000_000) * modele["prix_in"] + (
        tokens_out / 1_000_000
    ) * modele["prix_out"]


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY manquante. Faites : export ANTHROPIC_API_KEY=sk-ant-...")
        return

    print("=== Benchmark latence + qualité — API Claude (perturbation J2) ===")
    print(f"Protocole : {NB_APPELS} appels × {len(MODELES)} modèles × même cours de référence")
    print(f"Cours     : {TITRE_COURS}")
    print(f"Machine   : API cloud Anthropic (identique pour tous les modèles)\n")

    resultats = []
    cout_total = 0.0

    for modele in MODELES:
        print(f"--- {modele['label']} ({modele['id']}) ---")
        latences = []
        nb_valides = 0
        tokens_in_total = 0
        tokens_out_total = 0

        for i in range(1, NB_APPELS + 1):
            try:
                latence, valide, t_in, t_out = appel_anthropic(api_key, modele)
                latences.append(latence)
                nb_valides += 1 if valide else 0
                tokens_in_total += t_in
                tokens_out_total += t_out
                marque = "✓ JSON valide" if valide else "✗ JSON invalide"
                print(f"  Appel {i}/{NB_APPELS} : {latence:6.2f}s  {marque}")
            except requests.HTTPError as e:
                corps = e.response.text[:200] if e.response is not None else ""
                print(f"  Appel {i}/{NB_APPELS} : ÉCHEC HTTP {e}  {corps}")
            except Exception as e:
                print(f"  Appel {i}/{NB_APPELS} : ÉCHEC ({e})")

        if not latences:
            print("  Aucun appel réussi pour ce modèle.\n")
            continue

        cout = cout_estime(modele, tokens_in_total, tokens_out_total)
        cout_total += cout
        resultats.append(
            {
                "label": modele["label"],
                "p50": percentile(latences, 50),
                "p95": percentile(latences, 95),
                "moyenne": statistics.mean(latences),
                "valides": nb_valides,
                "total": len(latences),
                "cout": cout,
            }
        )
        print(
            f"  → p50={percentile(latences, 50):.2f}s  p95={percentile(latences, 95):.2f}s  "
            f"qualité={nb_valides}/{len(latences)} JSON valides  coût≈${cout:.4f}\n"
        )

    if not resultats:
        print("Aucun résultat exploitable.")
        return

    print("=== Tableau récapitulatif ===")
    entete = f"{'Modèle':<20}{'p50':>9}{'p95':>9}{'Moyenne':>10}{'Qualité':>10}{'Coût/run':>11}"
    print(entete)
    print("-" * len(entete))
    for r in resultats:
        cout_run = r["cout"] / r["total"]
        print(
            f"{r['label']:<20}"
            f"{r['p50']:>8.2f}s"
            f"{r['p95']:>8.2f}s"
            f"{r['moyenne']:>9.2f}s"
            f"{r['valides']}/{r['total']:>8}"
            f"{cout_run:>10.4f}$"
        )
    print("-" * len(entete))
    print(f"\nRAM / disque / GPU requis : AUCUN (API cloud, pas d'hébergement local)")
    print(f"Coût total de ce benchmark : ≈ ${cout_total:.4f}")

    # --- Garde-fou vs objectif produit (CA-J2-6 : ≤ 15 s) ---
    print("\n=== Objectif produit : temps de génération ≤ 15 s (CA-J2-6) ===")
    for r in resultats:
        statut = "✅" if r["p95"] <= 15 else "⚠️ "
        print(f"  {statut} {r['label']:<20} p95 = {r['p95']:.2f}s")


if __name__ == "__main__":
    main()
