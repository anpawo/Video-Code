# BETA TEST PLAN

**FROM AN IDEA TO A PRODUCT**

**Project name:** Video-Code  
**Repository:** [https://github.com/anpawo/Video-Code](https://github.com/anpawo/Video-Code)

---

## 1. Project Context, Objectives & Functioning

Video-Code est une bibliothèque open-source permettant de **générer, éditer et monter des vidéos à partir de code Python**.
Le projet vise à combiner la **puissance du scripting** avec la **précision du montage vidéo**, tout en restant accessible aux débutants et flexible pour les utilisateurs avancés.

La version beta se concentre sur :

* Une **API Python fonctionnelle**
* Des **composants vidéo de base**
* Des **transformations et effets simples**
* Un **rendu vidéo fiable via FFmpeg**

Le fonctionnement repose sur :

1. L’écriture d’un script Python utilisant l’API Video-Code
2. La création d’inputs (texte, image, vidéo, formes)
3. L’application de transformations
4. L’ajout des éléments à une timeline
5. La génération finale d’une vidéo exportée

---

## 2. User Roles

| User Role ID | User Role Name   | Description                                                              |
| ------------ | ---------------- | ------------------------------------------------------------------------ |
| UR-01        | Python Developer | Utilisateur à l’aise avec Python souhaitant créer des vidéos via du code |
| UR-02        | Content Creator  | Créateur de contenu cherchant à automatiser et personnaliser ses vidéos  |
| UR-03        | Technical User   | Utilisateur avancé testant les performances et la modularité du moteur   |

---

## 3. Feature Table (Organized by User Flow)

| Feature ID | User Role    | Feature Name          | Short Description                                     |
| ---------- | ------------ | --------------------- | ----------------------------------------------------- |
| F-01       | UR-01, UR-03 | Write video script    | Écrire un script Python utilisant l’API Video-Code    |
| F-02       | UR-01, UR-02 | Create media input    | Concréer des inputs vidéo, image ou texte             |
| F-03       | UR-01, UR-02 | Add input to timeline | Ajouter un input à la timeline de la vidéo            |
| F-04       | UR-01, UR-02 | Apply transformation  | Appliquer une transformation (move, scale, fade…)     |
| F-05       | UR-01        | Group inputs          | Grouper plusieurs inputs pour les manipuler ensemble  |
| F-06       | UR-01, UR-03 | Preview rendering     | Visualiser le rendu intermédiaire lors de l’exécution |
| F-07       | UR-01, UR-02 | Generate video file   | Générer une vidéo finale via FFmpeg                   |
| F-08       | UR-03        | Serialize project     | Sérialiser la scène vidéo pour réutilisation          |

---

## 4. Success Criteria Table

| Feature ID | Key Success Criteria                              | Indicator / Metric             | Result Achieved    |
| ---------- | ------------------------------------------------- | ------------------------------ | ------------------ |
| F-01       | Le script Python s’exécute sans erreur            | 10 exécutions, 0 crash         | Achieved           |
| F-02       | Les inputs sont visibles dans la vidéo            | 10 créations, 0 input manquant | Achieved           |
| F-03       | Les inputs apparaissent au bon moment             | Décalage temporel < 1 frame    | Achieved           |
| F-04       | Les transformations sont correctement appliquées  | 10 transformations testées     | Achieved           |
| F-05       | Les groupes se comportent comme une entité unique | 5 groupes testés               | Partially achieved |
| F-06       | Le rendu intermédiaire est exploitable            | Affichage < 1s/frame           | Partially achieved |
| F-07       | La vidéo finale est générée correctement          | 5 rendus complets, 0 échec     | Achieved           |
| F-08       | La scène peut être sauvegardée et rechargée       | 3 cycles save/load             | Achieved           |

---

## 5. Beta Scope Validation

Cette beta inclut uniquement les **fonctionnalités réellement implémentées et démontrables** lors de la soutenance :

* API Python fonctionnelle
* Inputs médias et texte
* Transformations de base
* Timeline et rendu vidéo
* Export FFmpeg

Les fonctionnalités suivantes **ne font pas partie de la beta** :

* Interface graphique complète
* Extension VS Code
* Interface no-code
* Système de plugins communautaires

---

## 6. Expected Outcome

Ce Beta Test Plan permet de :

* Valider que Video-Code offre une **expérience utilisateur complète minimale**
* Démontrer la **stabilité technique du moteur**
* Fournir une base solide pour l’intégration des retours utilisateurs
* Justifier la transition vers les prochaines phases du projet

Ce document servira de **référence officielle pour le jury Greenlight** afin d’évaluer la maturité et la crédibilité de la version beta.
