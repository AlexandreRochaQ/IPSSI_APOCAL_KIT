"""
Benchmark de latence pour la génération de quiz via Ollama (perturbation J2).

Usage :
    python benchmark_latence_ollama.py

Prérequis :
    pip install requests --break-system-packages
    Ollama doit tourner en local (ollama serve) avec le modèle déjà pull (ex: ollama pull llama3.1)
"""

import time
import statistics
import requests

# --- Paramètres à adapter à votre projet ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
NB_APPELS = 20  # 20 appels suffisent pour estimer la latence tout en ayant un temps de test raisonable.

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

# Remplacez ces deux variables par un VRAI titre + extrait de cours (300-500 mots),
# représentatif de ce qu'un étudiant uploaderait réellement (cf. F2)
# j'ai utilisé un cours généré par ChatGPT pour l'exemple.
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


# Reproduit exactement build_full_prompt() de quiz_prompt.py
PROMPT = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(COURS_EXEMPLE, TITRE_COURS)}"

# La température réelle du projet est fixée à 0.4 (cf. doc 02-llm-integration.md)
TEMPERATURE = 0.4


def appel_ollama(prompt: str) -> float:
    """Fait un appel à Ollama et retourne la latence en secondes."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
        },
    }
    debut = time.perf_counter()
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    fin = time.perf_counter()
    return fin - debut


def percentile(donnees: list[float], p: float) -> float:
    """Calcule le percentile p (entre 0 et 100) d'une liste de valeurs."""
    donnees_triees = sorted(donnees)
    k = (len(donnees_triees) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(donnees_triees) - 1)
    if f == c:
        return donnees_triees[f]
    return donnees_triees[f] + (donnees_triees[c] - donnees_triees[f]) * (k - f)


def main():
    latences = []
    print(f"Lancement de {NB_APPELS} appels au modèle '{MODEL}' via Ollama...\n")

    for i in range(1, NB_APPELS + 1):
        try:
            latence = appel_ollama(PROMPT)
            latences.append(latence)
            print(f"  Appel {i:2d}/{NB_APPELS} : {latence:6.2f}s")
        except Exception as e:
            print(f"  Appel {i:2d}/{NB_APPELS} : ÉCHEC ({e})")

    if not latences:
        print("\nAucun appel n'a réussi, vérifiez qu'Ollama tourne bien (ollama serve).")
        return

    print("\n--- Résultats ---")
    print(f"Nombre d'appels réussis : {len(latences)}")
    print(f"Min                     : {min(latences):.2f}s")
    print(f"Max                     : {max(latences):.2f}s")
    print(f"Moyenne                 : {statistics.mean(latences):.2f}s")
    print(f"p50 (médiane)           : {percentile(latences, 50):.2f}s")
    print(f"p95                     : {percentile(latences, 95):.2f}s")

    # Petit garde-fou par rapport à l'objectif produit (< 60s)
    p95 = percentile(latences, 95)
    if p95 > 60:
        print(f"\n⚠️  p95 ({p95:.2f}s) dépasse l'objectif produit de 60s.")
        print("   → matière à documenter dans l'ADR (changement de modèle, optimisation du prompt, cache, etc.)")
    else:
        print(f"\n✅ p95 ({p95:.2f}s) respecte l'objectif produit de 60s.")


if __name__ == "__main__":
    main()
