# Benchmark LLM Locale

Ce document sert de guide d'utilisation du script de benchmark de la LLM locale du projet.

Comment lancer le benchmark, comment interpréter les résultats et comment ajouter de nouveaux tests.

## Prérequis

- Avoir suivi le guide d'installation et de configuration du projet (le README principal du projet).
- Avoir Python installé sur votre machine.
- Avoir tout les conteneurs Docker du projet lancés.

## TLDR du guide d'installation du projet

- 🟢 Lancer l'application en une commande

Plutôt que les 4 étapes manuelles ci-dessus, un **script de lancement par OS**
fait tout d'un coup : crée le `.env` si besoin → **build** les images →
**(re)lance** les conteneurs → attend que le backend réponde → applique les
**migrations** → insère les **données de démo** → vérifie le **modèle LLM** (et
**propose de le télécharger** s'il manque) → affiche les URLs. Lançable depuis
n'importe où (le script se replace à la racine du projet).

| Système | Commande |
|---|---|
| **Linux** | `bash scripts/start-linux.sh` |
| **macOS** | `bash scripts/start-macos.sh` |
| **Windows (PowerShell)** | `powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1` |

## Étape 1

Ouvrir PowerShell dans le dossier `backend/llm/services`.

Exécuter le script :

```
python benchmark_latence_ollama.py
```

## Fonctionnement du benchmark

Le fichier `quiz_prompt.py` contient les prompts utilisés pour générer le quiz. C'est ce fichier qui est utilisé lorsque l'utilisateur va générer un quiz via l'interface web.

`benchmark_latence_ollama.py` se base sur ce même fichier en reproduisant le même scénario. Il se connecte directement au conteneur Docker qui contient le modèle LLM (Ollama) localement et va effectuer 20 requêtes de génération de quiz avec les prompts définis dans `quiz_prompt.py`.

Puis il calcule le temps moyen de réponse et l'écart type pour chaque prompt, et va évaluer la latence en se basant sur p50/p95, puis générer un rapport du benchmark avec un résultat positif ou négatif qui sera documenté dans l'ADR.

## Exemple d'utilisation du script benchmark_latence_ollama.py

```
PS C:\Users\emmel\PhpstormProjects\IPSSI_APOCAL_KIT\backend\llm\services> python benchmark_latence_ollama.py
Lancement de 20 appels au modèle 'llama3.1:8b' via Ollama...

Appel  1/20 : ÉCHEC (HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120))
Appel  2/20 : ÉCHEC (HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120))
Appel  3/20 :  91.25s
Appel  4/20 : 102.35s
Appel  5/20 : ÉCHEC (HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120))
Appel  6/20 : ÉCHEC (HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120))
Appel  7/20 :  89.74s
Appel  8/20 :  89.16s
Appel  9/20 : 114.92s
Appel 10/20 : ÉCHEC (HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120))
Appel 11/20 :  88.37s
Appel 12/20 :  79.20s
Appel 13/20 :  89.15s
Appel 14/20 : 109.27s
Appel 15/20 :  97.88s
Appel 16/20 : 103.30s
Appel 17/20 : ÉCHEC (HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120))
Appel 18/20 :  90.33s
Appel 19/20 : 100.55s
Appel 20/20 : 117.56s

--- Résultats ---
Nombre d'appels réussis : 14
Min                     : 79.20s
Max                     : 117.56s
Moyenne                 : 97.36s
p50 (médiane)           : 94.57s
p95                     : 115.84s

⚠️  p95 (115.84s) dépasse l'objectif produit de 60s.
→ matière à documenter dans l'ADR (changement de modèle, optimisation du prompt, cache, etc.)
```
