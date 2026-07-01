
# Registre des traitements et demandes d’accès — SAR / RGPD

## Objectif

Ce document regroupe deux éléments de conformité pour EduTutor IA :

1. Un extrait du registre des traitements, afin de documenter les principales données personnelles traitées par la plateforme.
2. Un registre des demandes RGPD, afin de tracer les demandes d’accès, d’export, de rectification ou de suppression formulées par les utilisateurs.

L’objectif est de démontrer que l’équipe maîtrise les données collectées, les finalités de traitement, les bases légales, les durées de conservation et le suivi des demandes utilisateurs.

---

## 1. Extrait du registre des traitements — Article 30 RGPD

| Traitement                    | Finalité                                                                         | Données concernées                                                          | Personnes concernées      | Base légale                                     | Conservation                                  | Destinataires / sous-traitants               |
| ----------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------ | --------------------------------------------- | -------------------------------------------- |
| Gestion des comptes           | Création et accès au compte utilisateur                                         | Email, identifiant, date de création, dernière connexion                    | Étudiants, enseignants    | Exécution du service                            | Durée du compte + 12 mois après suppression | Équipe EduTutor IA, hébergement applicatif |
| Upload de cours               | Permettre la génération de quiz à partir de contenus fournis                   | Fichiers PDF, textes de cours, métadonnées de dépôt                       | Utilisateurs authentifiés | Exécution du service / consentement utilisateur | Tant que le compte est actif                  | Backend EduTutor IA, stockage applicatif     |
| Génération de quiz          | Produire des questions de révision personnalisées                               | Contenu du cours, questions générées, réponses proposées, bonne réponse | Étudiants, enseignants    | Exécution du service                            | Tant que le compte est actif                  | Backend EduTutor IA, modèle LLM local       |
| Suivi des réponses et scores | Suivre la progression de l’utilisateur                                           | Réponses choisies, score obtenu, date du quiz                                | Étudiants                 | Exécution du service                            | Tant que le compte est actif                  | Backend EduTutor IA                          |
| Signalements utilisateur      | Corriger les erreurs, améliorer le service, traiter les contenus problématiques | Message de signalement, type d’erreur, date, utilisateur concerné           | Utilisateurs authentifiés | Intérêt légitime                              | 3 ans maximum                                 | Équipe produit / support                    |
| Logs d’audit                 | Assurer la sécurité, la traçabilité et la preuve des actions sensibles        | Actions utilisateur, dates, exports, demandes RGPD, événements sécurité   | Utilisateurs authentifiés | Intérêt légitime / obligation légale         | 12 mois                                       | Administrateurs habilités                   |
| Demandes RGPD / SAR           | Gérer les droits d’accès, export, rectification et effacement                  | Identité du demandeur, type de demande, statut, dates, hash d’export        | Utilisateurs demandeurs    | Obligation légale                               | 3 ans                                         | DPO fictif, équipe EduTutor IA              |

---

## 2. Registre des demandes RGPD — Modèle DataRequest

Le modèle `DataRequest` permet de conserver une trace des demandes d’accès, d’export, de rectification ou de suppression.

Il sert à démontrer que l’équipe a bien reçu, traité et répondu aux demandes RGPD dans un délai maîtrisé.

| Champ            | Type              | Description                                                  |
| ---------------- | ----------------- | ------------------------------------------------------------ |
| id               | UUID / integer    | Identifiant unique de la demande                             |
| user             | ForeignKey User   | Utilisateur authentifié ayant fait la demande               |
| request_type     | enum              | Type de demande : access, export, deletion, rectification    |
| status           | enum              | Statut : received, in_progress, completed, rejected          |
| requested_at     | datetime          | Date de réception de la demande                             |
| processed_at     | datetime nullable | Date de traitement effectif                                  |
| response_sent_at | datetime nullable | Date d’envoi de la réponse                                 |
| export_format    | string            | Format fourni : json, csv, zip                               |
| export_hash      | string nullable   | Hash SHA-256 du fichier exporté                             |
| notes            | text nullable     | Commentaires internes sur le traitement                      |
| handled_by       | string nullable   | Responsable ou membre de l’équipe ayant traité la demande |

---

## 3. Statuts possibles

| Statut      | Signification                       |
| ----------- | ----------------------------------- |
| received    | Demande reçue                      |
| in_progress | Demande en cours de traitement      |
| completed   | Réponse envoyée à l’utilisateur |
| rejected    | Demande rejetée avec justification |

---

## 4. Exemple d’entrée SAR

| Champ            | Valeur                                                                                               |
| ---------------- | ---------------------------------------------------------------------------------------------------- |
| user             | hugo.petit@test.local                                                                                |
| request_type     | export                                                                                               |
| status           | completed                                                                                            |
| requested_at     | 2026-07-01 10:30                                                                                     |
| processed_at     | 2026-07-01 14:00                                                                                     |
| response_sent_at | 2026-07-01 14:15                                                                                     |
| export_format    | json                                                                                                 |
| export_hash      | sha256:xxxxxxxx                                                                                      |
| notes            | Export complet généré pour les données utilisateur, cours, quiz, réponses, signalements et logs |
| handled_by       | Équipe EduTutor IA                                                                                  |

---

## 5. Points de vigilance

- Ne jamais exporter les données d’un autre utilisateur.
- Filtrer systématiquement toutes les requêtes par `request.user`.
- Ne jamais utiliser de requêtes globales du type `objects.all()` dans l’endpoint d’export.
- Vérifier que l’export contient bien les catégories demandées : compte, cours, quiz, réponses, signalements et logs.
- Conserver une preuve du fichier exporté via un hash SHA-256.
- Ne pas conserver le fichier exporté indéfiniment.
- Journaliser la date de réception, la date de traitement et la date de réponse.
- Prévoir une suppression ou anonymisation des données lorsque la durée de conservation est atteinte.

---

## 6. Lien avec les droits RGPD

Ce registre contribue à la gestion des droits suivants :

- Droit d’accès — Article 15 RGPD.
- Droit de rectification — Article 16 RGPD.
- Droit à l’effacement — Article 17 RGPD.
- Droit à la limitation du traitement — Article 18 RGPD.
- Droit à la portabilité — Article 20 RGPD.

Les exports doivent être fournis dans un format structuré, couramment utilisé et lisible par machine, par exemple JSON ou CSV.