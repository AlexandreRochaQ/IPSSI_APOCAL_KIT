
# Note de priorisation RGPD — Perturbation J3-bis

## 1. Contexte

Une demande d’accès aux données personnelles a été formulée par Hugo Petit au titre de l’article 15 du RGPD.

L’utilisateur demande à recevoir l’ensemble des données personnelles associées à son compte `hugo.petit@test.local`, dans un format structuré, couramment utilisé et lisible par machine, comme JSON ou CSV.

Les catégories demandées sont les suivantes :

- données de compte ;
- cours et textes uploadés ;
- quiz générés ;
- réponses aux quiz et scores ;
- signalements éventuels ;
- logs d’audit.

L’article 15 RGPD prévoit bien le droit pour une personne d’obtenir l’accès aux données personnelles la concernant ainsi qu’une copie de ces données. Le RGPD prévoit également d’autres droits associés, notamment la rectification, l’effacement, la limitation du traitement et la portabilité. [1](https://ufukozen.com/model/phi-3-mini)[2](https://medium.com/towards-agi/llama-3-2-benchmark-insights-and-revolutionizing-edge-ai-and-vision-88542fe3dc0d)

Cette perturbation arrive en parallèle de la livraison MVP et de la correction de la vulnérabilité de prompt injection. L’objectif est donc de démontrer une posture sérieuse : données identifiées, exportables, filtrées par utilisateur, traçables et accompagnées d’une politique de rétention.

---

## 2. Priorités MVP

Compte tenu du temps disponible, l’équipe priorise les éléments suivants.

| Priorité | Élément                                | Objectif                                                           | Statut                       |
| --------- | ---------------------------------------- | ------------------------------------------------------------------ | ---------------------------- |
| P0        | Endpoint`GET /api/accounts/me/export/` | Permettre à l’utilisateur authentifié d’exporter ses données  | À implémenter / En cours   |
| P0        | Filtrage strict par`request.user`      | Empêcher toute fuite de données entre utilisateurs               | Obligatoire                  |
| P0        | Export JSON                              | Fournir un format structuré et lisible par machine                | Obligatoire                  |
| P1        | Export CSV                               | Fournir un second format de portabilité                           | À faire si temps disponible |
| P1        | Bouton “Exporter mes données”         | Rendre l’export accessible depuis le frontend authentifié        | À implémenter              |
| P1        | Modèle`DataRequest`                   | Tracer la demande SAR : demandeur, date, statut, hash de l’export | À implémenter              |
| P1        | Politique de rétention                  | Documenter les durées, bases légales et suppressions             | Réalisé                    |
| P1        | Réponse écrite à Hugo Petit           | Fournir une réponse professionnelle et structurée                | Réalisé                    |

---

## 3. Arbitrage MVP vs conformité complète

L’équipe distingue deux niveaux de conformité.

### Pour le MVP

Les éléments indispensables sont :

- export JSON complet ;
- filtrage strict des données par utilisateur connecté ;
- inclusion des 6 catégories demandées ;
- audit trail de la demande via `DataRequest` ;
- politique de rétention documentée ;
- réponse écrite structurée à Hugo Petit.

### Après le MVP

Les éléments suivants sont reportés après la livraison MVP :

- interface d’administration complète des demandes RGPD ;
- automatisation complète de la purge des données ;
- export ZIP structuré avec plusieurs fichiers JSON ;
- génération automatique du hash de chaque export ;
- DPIA / AIPD complète avant ouverture publique ;
- revue juridique complète par un DPO réel.

---

## 4. Risques identifiés et mesures de réduction

| Risque                                        | Impact                                         | Mesure de réduction                                                                 |
| --------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------ |
| Exporter les données d’un autre utilisateur | Violation grave de données personnelles       | Filtrage strict par`request.user` sur toutes les requêtes                         |
| Export incomplet                              | Non-respect de l’esprit de l’article 15 RGPD | Vérification des 6 catégories : compte, cours, quiz, réponses, signalements, logs |
| Format non exploitable                        | Portabilité insuffisante                      | Export JSON obligatoire, CSV en second format si possible                            |
| Absence de preuve de traitement               | Difficulté à démontrer la conformité       | Modèle`DataRequest` avec statut, dates et hash d’export                          |
| Conservation excessive                        | Risque de non-conformité                      | Politique de rétention avec durées précises                                       |
| Suppression non maîtrisée                   | Non-respect potentiel de l’article 17 RGPD    | Procédure de suppression ou anonymisation documentée                               |
| Retard de réponse                            | Risque conformité et image négative          | Réponse préparée sous 48h pour le POC                                             |

---

## 5. Position sur le registre des traitements

Le cours rappelle que le registre des traitements est le document central permettant de démontrer la conformité RGPD. Il doit préciser, pour chaque traitement, la finalité, les catégories de données, les personnes concernées, la base légale, les destinataires, les durées de conservation et les mesures de sécurité.

Pour le MVP EduTutor IA, l’équipe produit un extrait de registre couvrant les traitements principaux :

- gestion des comptes ;
- upload de cours ;
- génération de quiz ;
- suivi des réponses et scores ;
- signalements ;
- logs d’audit ;
- demandes RGPD / SAR.

Ce registre est volontairement limité au périmètre MVP, mais il constitue une base pour un registre complet avant toute ouverture publique.

---

## 6. Position sur la DPIA / AIPD

EduTutor IA traite des données d’étudiants : compte utilisateur, cours uploadés, quiz générés, réponses, scores et logs d’audit.

Ces données ne sont pas nécessairement sensibles au sens strict du RGPD, mais elles peuvent révéler des informations sur le niveau, les difficultés, les habitudes d’apprentissage et les contenus étudiés par un utilisateur.

À ce stade MVP, l’équipe ne réalise pas une DPIA complète. En revanche, elle identifie les risques principaux et prévoit les mesures suivantes :

| Risque DPIA identifié                         | Mesure prévue                                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- |
| Fuite de données entre utilisateurs           | Filtrage strict par`request.user`                                                   |
| Collecte excessive                             | Principe de minimisation appliqué aux données exportées et conservées             |
| Conservation trop longue                       | Politique de rétention documentée                                                   |
| Absence de traçabilité SAR                   | Modèle`DataRequest` persisté                                                      |
| Données de cours potentiellement personnelles | Suppression possible sur demande Art. 17                                              |
| Export non sécurisé                          | Génération d’un hash de fichier et suppression de l’export après durée limitée |

Décision : une DPIA complète devra être planifiée avant une ouverture publique ou une montée en charge significative. Pour le MVP, l’équipe documente une première posture de conformité : registre, export utilisateur, audit trail SAR, politique de rétention et réponse structurée.

---

## 7. Décision de priorisation

Pour la livraison MVP, l’équipe décide de prioriser :

1. un export JSON complet des données utilisateur ;
2. un filtrage strict par utilisateur authentifié ;
3. la traçabilité de la demande via `DataRequest` ;
4. une politique de rétention documentée ;
5. une réponse écrite professionnelle à Hugo Petit.

Les fonctionnalités plus avancées, comme une interface d’administration complète, une DPIA détaillée ou une automatisation complète de la purge, sont reportées après le MVP.

Cette décision permet de répondre à la demande SAR dans le délai annoncé, tout en évitant de bloquer la livraison MVP sur une conformité exhaustive impossible à finaliser dans la journée.