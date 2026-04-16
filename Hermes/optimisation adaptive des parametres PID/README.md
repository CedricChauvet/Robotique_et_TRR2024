
# Optimisation Adaptative des Paramètres PID par Rétropropagation de Gradient sur Système Physique Réel

**Application : Véhicule RC autonome — Moteur DC brushed / Pont H IBT-2 / Teensy**

---

## Table des matières

1. [Concept — Analogie avec la Backpropagation](#1-concept--analogie-avec-la-backpropagation)
2. [Description du Matériel](#2-description-du-matériel)
3. [Modèle Mathématique du Système](#3-modèle-mathématique-du-système)
4. [Deux Configurations de Test](#4-deux-configurations-de-test)
5. [Analyse des Phases de Conduite](#5-analyse-des-phases-de-conduite)
6. [Anticipation par Télémètre](#6-anticipation-par-télémètre)
7. [Modes de Freinage — IBT-2](#7-modes-de-freinage--ibt-2)
8. [Algorithme SPSA](#8-algorithme-spsa)
9. [Simulation — Complément au Plan SPSA](#9-simulation--complément-au-plan-spsa)
10. [Prochaines Étapes](#10-prochaines-étapes)
- [Annexe — Paramètres de Simulation par Défaut](#annexe--paramètres-de-simulation-par-défaut)

---

## 1. Concept — Analogie avec la Backpropagation

> 📍 **Contexte : Les deux** — Simulation et Système réel (model-free)

L'idée centrale est d'appliquer le même mécanisme de descente de gradient qu'un réseau de neurones, mais en remplaçant les poids par les paramètres P, I et D d'un contrôleur PID. Le système physique (moteur + transmission + masse) joue le rôle du réseau, et l'odométrie fournit le signal d'erreur équivalent à la loss function.

| Réseau de neurones | PID adaptatif |
|---|---|
| Poids W | Paramètres P, I, D |
| Couches | Moteur + mécanique + odométrie |
| Loss (MSE) | Erreur vitesse mesurée / consigne |
| Backpropagation | Estimation SPSA du gradient |
| Descente de gradient | Mise à jour itérative de θ = [P, I, D] |

### 1.1 Problème central : différentiabilité

En mode **model-free** (système physique réel), on ne peut pas calculer `∂sortie/∂(P,I,D)` analytiquement. La solution retenue est l'estimation numérique du gradient par perturbation simultanée des paramètres — algorithme **SPSA**.

---

## 2. Description du Matériel

### 2.1 Chaîne de contrôle

| Composant | Rôle | Remarques |
|---|---|---|
| Teensy | Microcontrôleur | Génère le signal PWM |
| IBT-2 (BTS7960) | Pont en H | Pilotage bidirectionnel du moteur |
| Moteur DC brushed | Actionneur | Modèle à identifier |
| Capteurs à effet Hall (×2 par roue) | Odométrie | Mesure de vitesse sur la roue |
| Batterie LiPo 2S | Alimentation | 7.4V nominal, 8.4V plein |

L'odométrie est réalisée par deux capteurs à effet Hall positionnés face à face sur une roue, à égale distance l'un de l'autre. Chaque capteur déclenche une interruption sur le Teensy à chaque demi-tour de roue. Le Teensy reçoit donc **2 fronts montants par tour**, ce qui constitue la résolution de base de la mesure de vitesse.

### 2.2 Paramètres physiques connus

| Paramètre | Valeur | Source |
|---|---|---|
| Tension batterie | 7.4V (nominal) | LiPo 2S |
| Diamètre des roues | 7.2 cm → rayon 3.6 cm | Mesure |
| Masse du véhicule | ~1 kg | Estimation |
| Rapport de transmission G | **Information manquante** | À mesurer sur le robot |
| Vitesse virage | 8 km/h | Contrainte opérationnelle |
| Vitesse ligne droite | 14 km/h | Contrainte opérationnelle |

---

## 3. Modèle Mathématique du Système

> 📍 **Contexte : Simulation uniquement** — ce modèle sert à construire le robot virtuel. En mode réel (model-free), il n'est pas utilisé directement ; c'est le système physique lui-même qui joue ce rôle.

### 3.1 Équation électrique du moteur

Le moteur DC brushed est décrit par deux équations couplées. L'équation électrique gouverne le courant d'armature :

```
V(t) = R·i(t) + L·(di/dt) + Ke·ω(t)
```

| Terme | Nom | Rôle |
|---|---|---|
| R·i(t) | Chute résistive | Tension perdue en chaleur dans les bobinages |
| L·di/dt | Chute inductive | Retard du courant lors des variations rapides |
| Ke·ω(t) | Force contre-électromotrice (fcem) | Tension générée par la rotation du rotor |

**R·i(t)** représente la tension consommée par la résistance des bobinages de cuivre. Elle est entièrement dissipée en chaleur et constitue la principale perte du moteur. Plus le courant est élevé (fort couple demandé), plus cette perte est importante. R se mesure simplement à l'ohmmètre, bornes moteur déconnectées.

**L·di/dt** représente la tension nécessaire pour faire varier le courant dans les bobinages. L'inductance L s'oppose aux changements rapides de courant — c'est elle qui provoque un retard entre la commande PWM et la réponse en courant. En pratique sur un moteur RC brushed, L est très faible (< 1 mH) et ce terme devient négligeable en régime quasi-statique.

**Ke·ω(t)** est la force contre-électromotrice (fcem). Quand le moteur tourne, il se comporte simultanément comme un générateur et produit une tension proportionnelle à sa vitesse angulaire. Cette tension s'oppose à la tension d'alimentation, ce qui limite naturellement le courant et donc le couple à mesure que la vitesse augmente. C'est le mécanisme intrinsèque de régulation du moteur DC brushed — à ne pas confondre avec les frottements, qui sont un phénomène mécanique distinct.

### 3.2 Équation mécanique du moteur

```
J·(dω/dt) = Kt·i(t) - B·ω(t) - Tf
```

| Terme | Nom | Nature |
|---|---|---|
| J·dω/dt | Inertie totale × accélération angulaire | Résistance au changement de vitesse |
| Kt·i(t) | Couple moteur | Force motrice produite par le courant |
| B·ω(t) | Frottement visqueux | Résistance proportionnelle à la vitesse |
| Tf | Frottement sec | Résistance constante, indépendante de ω |

**J·dω/dt** est le terme d'inertie. J représente la résistance totale du système au changement de vitesse — l'équivalent mécanique de la masse. Il regroupe l'inertie du rotor, des roues et de la masse du véhicule ramenée à l'axe. Plus J est grand (véhicule chargé), plus il faut de couple pour accélérer ou décélérer.

**Kt·i(t)** est le couple produit par le moteur, directement proportionnel au courant. Kt est la constante de couple (N·m/A). En pratique pour un moteur DC, Kt est numériquement égal à Ke lorsque les deux sont exprimés en unités SI cohérentes. C'est le seul terme moteur de l'équation — tout le reste s'y oppose.

**B·ω(t)** est le frottement visqueux, proportionnel à la vitesse de rotation. Il modélise les résistances qui augmentent avec la vitesse : frottement de l'air, viscosité des lubrifiants dans les roulements. Son effet est faible à basse vitesse et croît linéairement.

**Tf** est le frottement sec (ou frottement de Coulomb), constant quelle que soit la vitesse. Il représente la résistance mécanique incompressible : frottement des balais sur le collecteur, résistance initiale des roulements, jeu dans la transmission. Il est responsable de la zone morte à faible couple : le moteur ne tourne pas tant que `Kt·i < Tf`.

### 3.3 Effet du rapport de transmission G

```
ω_moteur    = G × ω_roue
T_roue      = G × Kt × i        (couple multiplié)
J_vu_moteur = J_total / G²      (inertie réduite)
```

G influence directement la réactivité du système et donc les valeurs optimales de P, I, D. Il sera déterminé expérimentalement en comptant les tours du moteur pour un tour de roue.

---

## 4. Deux Configurations de Test

> 📍 **Contexte : Les deux** — En simulation, ces configurations correspondent à deux jeux de paramètres physiques distincts chargés dans le modèle. En mode réel (model-free), elles correspondent à deux situations expérimentales concrètes sur le robot physique.

### 4.1 Comparaison générale

| Paramètre | Banc (roues libres) | Piste (véhicule complet) |
|---|---|---|
| Inertie J | Faible (roues seules) | Grande (masse véhicule) |
| Frottement | Roulements seuls | Pneu/sol + résistances |
| Temps de réponse | Rapide | Plus lent |
| Perturbations | Nulles | Relief, virages, pente |
| P, I, D optimaux | Agressifs | Plus doux, plus de D |

**Stratégie recommandée :** utiliser le banc comme point de départ (*warm start*) pour l'optimisation sur piste. En simulation, on charge J_banc puis J_piste. En mode réel, on fait tourner SPSA d'abord sur banc, puis on utilise ces P\*, I\*, D\* comme initialisation pour les runs sur piste — ce qui réduit le nombre d'itérations nécessaires et limite les risques lors des premiers essais en conditions réelles.

### 4.2 Équation mécanique sur banc

> 📍 **Contexte : Simulation** (J_banc paramètre du modèle) — **Système réel** (comportement observé sur banc)

Sur banc, le moteur entraîne uniquement les roues dans le vide. La masse du véhicule n'est pas engagée et il n'y a pas de contact pneu/sol. L'équation mécanique se simplifie :

```
J_banc·(dω/dt) = Kt·i(t) - B_banc·ω(t) - Tf_banc
```

| Terme | Composition | Valeur relative |
|---|---|---|
| J_banc | Inertie rotor/G² + inertie roues seules | Faible — système léger et réactif |
| B_banc | Frottement visqueux des roulements seuls | Très faible |
| Tf_banc | Frottement sec des roulements + balais | Faible, reproductible |

Le banc est le contexte idéal pour identifier R, Ke et Kt : le système est stable, les perturbations sont nulles et les conditions sont reproductibles. En revanche, J_banc est trop faible pour être représentatif de la piste — les P\*, I\*, D\* obtenus sur banc seront trop agressifs en conditions réelles.

### 4.3 Équation mécanique sur piste

> 📍 **Contexte : Simulation** (J_piste paramètre du modèle) — **Système réel** (comportement observé sur piste)

Sur piste, la masse complète du véhicule est engagée via les roues au contact du sol. L'équation mécanique intègre toutes les résistances réelles :

```
J_piste·(dω/dt) = Kt·i(t) - B_piste·ω(t) - Tf_piste
```

| Terme | Composition | Valeur relative |
|---|---|---|
| J_piste | J_banc + M·r² (masse véhicule ramenée à l'axe roue) | Dominant — beaucoup plus grand que J_banc |
| B_piste | Roulements + résistance aérodynamique + roulement pneu | Modéré, variable selon la surface |
| Tf_piste | Tf_banc + frottement pneu/sol + résistances transmission | Plus élevé, variable selon la surface |

La différence principale avec le banc est l'inertie J_piste, dominée par le terme `M·r² = 1 × 0.036² = 0.0013 kg·m²` qui représente la contribution de la masse du véhicule. Le système est plus lent à accélérer et à décélérer, ce qui justifie un réglage PID distinct et plus doux.

---

## 5. Analyse des Phases de Conduite

> 📍 **Contexte : Les deux** — la stratégie de course et la loss function s'appliquent identiquement en simulation et sur le robot réel.

### 5.1 Exemple de stratégies de course

| Phase | Criticité | Contrainte principale | Paramètre PID clé |
|---|---|---|---|
| Maintien 8 km/h (virage) | HAUTE | Pas d'overshoot → adhérence | P + I |
| Maintien 14 km/h (ligne) | MOYENNE | Rejet perturbations | I |
| Décélération 14→8 km/h | CRITIQUE | Terminée avant le virage | D + anticipation |
| Accélération 8→14 km/h | BASSE | Le plus vite possible | P (saturation PWM) |

### 5.2 Un seul PID ou gain scheduling ? — Discussion

L'utilisation d'un seul jeu de paramètres PID est la solution la plus simple et constitue le point de départ recommandé. SPSA trouvera un compromis acceptable entre les deux régimes. C'est l'approche retenue dans un premier temps.

Le *gain scheduling* (deux jeux P,I,D commutés selon la consigne) reste une option d'amélioration si les performances du PID unique s'avèrent insuffisantes, notamment si l'overshoot en virage ne peut pas être éliminé avec un seul réglage. Il n'est pas implémenté d'emblée.

### 5.3 La Loss Function — définition et choix

La **loss function** (ou fonction de coût) est le critère numérique que SPSA cherche à minimiser. Elle traduit en un seul scalaire la qualité du comportement du véhicule sur un épisode de test. Plus la loss est faible, meilleur est le réglage PID.

Trois formulations classiques existent, chacune avec un comportement différent face à l'erreur `e(t) = vitesse_mesurée - consigne` :

| Nom | Formule | Comportement |
|---|---|---|
| ISE — Integral of Squared Error | ∫ e² dt | Pénalise fortement les grandes erreurs. Favorise la réactivité. |
| IAE — Integral of Absolute Error | ∫ \|e\| dt | Pénalise toutes les erreurs également. Plus robuste au bruit. |
| ITAE — Integral of Time × Absolute Error | ∫ t·\|e\| dt | Pénalise les erreurs qui persistent dans le temps. Favorise un bon settling final. |

Pour ce projet, l'**ITAE** est recommandée en régime de maintien car elle tolère une erreur transitoire au début de l'épisode (démarrage du PID) mais pénalise fortement toute erreur résiduelle. En virage, une pondération asymétrique peut être ajoutée si le gain scheduling n'est pas retenu : les dépassements vers le haut (trop vite) sont pénalisés plus fortement que les déficits de vitesse.

---

## 6. Anticipation par Télémètre

> 📍 **Contexte : Les deux** — En simulation, la distance au virage est calculée depuis la position du robot virtuel sur le circuit modélisé. En mode réel, elle est mesurée directement par le capteur physique.

L'ajout de télémètres frontaux transforme le système d'un contrôle réactif en contrôle prédictif. La décélération est déclenchée en fonction de la distance mesurée au prochain virage, transformant un step brutal en rampe contrôlée.

### 6.1 Vecteur de paramètres étendu

SPSA peut optimiser simultanément 7 paramètres avec le même coût de **2 runs par itération** :

```python
θ = [P_rapide, I_rapide, D_rapide,    # régime ligne droite
     P_lent,   I_lent,   D_lent,      # régime virage
     d_seuil]                         # distance de déclenchement
```

### 6.2 Loss function pondérée par la distance

L'idée est d'intégrer directement la criticité de la position dans le calcul de la loss. Une erreur de vitesse commise loin d'un virage est moins grave que la même erreur commise à l'entrée d'un virage où l'adhérence est sollicitée.

La pondération est construite à partir de la distance mesurée par le télémètre : plus le véhicule est proche d'un virage, plus le poids appliqué à l'erreur est élevé. La fonction exponentielle choisie assure une montée progressive du poids qui s'accélère dans les derniers centimètres avant le virage.

```
poids_securite = 1 + α × exp(-d_telemetre / d_critique)
                 ↑            ↑                ↑
            base = 1   amplitude        distance de référence

loss = Σ  t × |erreur(t)| × poids_securite(t)
        ↑       ↑                  ↑
    ITAE    erreur vitesse    pondération position
```

- **Loin du virage** (d grand) : poids ≈ 1 → la loss est l'ITAE standard
- **Près du virage** (d petit) : poids >> 1 → la moindre erreur est fortement pénalisée

SPSA apprend ainsi naturellement à prioriser la précision aux endroits critiques, sans qu'on ait besoin de lui décrire la géométrie de la piste.

---

## 7. Modes de Freinage — IBT-2

> 📍 **Contexte : Système réel (model-free) uniquement** — le freinage est un comportement physique à caractériser expérimentalement. En simulation, une décélération équivalente est modélisée via un couple résistant appliqué à l'équation mécanique.

| Mode | Commande IBT-2 | Efficacité | Risque |
|---|---|---|---|
| Coast (roue libre) | R_EN=0, L_EN=0 | Très faible | Aucun |
| **Frein dynamique** | RPWM=0, LPWM=0 (EN actifs) | Modérée ✓ | **Aucun** |
| Plugging (inversion) | Tension inverse pleine | Très forte | ⚠️ Pic courant fatal pour IBT-2 |
| Régénératif dosé | Duty cycle inverse modulé | Forte ✓ | Faible |

### 7.1 Expériences recommandées

Avant toute optimisation SPSA, il est indispensable de caractériser expérimentalement la capacité de freinage réelle du système. Les expériences suivantes sont proposées par ordre de priorité, à réaliser d'abord sur banc puis sur piste.

**Expérience 1 — Coast pur :** lancer le moteur à 14 km/h, couper la commande, mesurer la distance et le temps pour atteindre 8 km/h. C'est le plancher de référence — toute autre méthode doit faire mieux.

**Expérience 2 — Frein dynamique (prioritaire) :** même protocole, appliquer `RPWM=0 / LPWM=0` avec les enables actifs. Mesurer le gain en décélération par rapport au coast. C'est le mode le plus pertinent car il est sûr, reproductible et directement exploitable dans la boucle SPSA.

**Expérience 3 — Régénératif dosé à 25%, 50%, 75% de duty cycle inverse :** mesurer la courbe décélération/duty pour établir la relation de commande.

Ces trois expériences sont implémentées dans le fichier :

```
freinage_caracterisation.py
```

Ce script sera développé ultérieurement. Il produira les courbes vitesse/temps pour chaque mode et calculera automatiquement la décélération moyenne en m/s².

### 7.2 Distance de freinage — estimation

Le résultat de ces expériences alimentera directement le paramètre `d_seuil` du télémètre. La relation théorique est :

```
d_frein = (v_initiale² - v_finale²) / (2 × a_mesurée)

→ de 14 km/h à 8 km/h avec a = 2.0 m/s²  :  d ≈ 0.84 m   (frein dynamique)
→ de 14 km/h à 8 km/h avec a = 0.4 m/s²  :  d ≈ 4.2 m   (coast seul)
```

L'écart entre les deux cas illustre l'importance de connaître le mode de freinage avant de paramétrer le télémètre.

---

## 8. Algorithme SPSA

> 📍 **Contexte : Les deux** — l'algorithme SPSA est identique en simulation et en mode réel. La seule différence est la nature de `run_episode()` : en simulation elle intègre le modèle ODE ; en mode réel elle envoie les commandes PWM et lit l'odométrie Hall.

### 8.1 Définition et origine

**SPSA** est l'acronyme de **Simultaneous Perturbation Stochastic Approximation** — *Approximation Stochastique par Perturbation Simultanée*. L'algorithme a été développé par James Spall (Johns Hopkins University, 1992) comme solution au problème d'estimation de gradient dans les systèmes où la fonction à optimiser n'est pas analytiquement dérivable.

Sa propriété fondamentale est remarquable : quel que soit le nombre de paramètres à optimiser (ici 3 ou 7), **il suffit de deux évaluations de la fonction coût par itération**. Un gradient estimé par différences finies classiques nécessiterait 2×N évaluations (N = nombre de paramètres). SPSA conserve la même précision asymptotique avec un coût constant.

### 8.2 Principe de fonctionnement

À chaque itération, SPSA tire un vecteur de perturbation aléatoire Δ dont chaque composante vaut +1 ou -1 avec probabilité égale. Il déplace simultanément tous les paramètres dans cette direction (run +) puis dans la direction opposée (run -), et estime le gradient à partir de la différence des deux mesures de loss :

```python
θ = [P, I, D]                                    # vecteur paramètres
Δ = [±1, ±1, ±1]  (tirage aléatoire)            # direction perturbation

Run 1 :  Loss⁺ = run_episode(θ + c·Δ)
Run 2 :  Loss⁻ = run_episode(θ - c·Δ)

Gradient estimé :  ĝᵢ = (Loss⁺ - Loss⁻) / (2·c·Δᵢ)  pour chaque i
Mise à jour      :  θ  ← θ - α · ĝ
```

L'intuition est la suivante : en perturbant tous les paramètres en même temps, on mesure comment la loss réagit globalement à un déplacement dans l'espace des paramètres. La direction aléatoire Δ garantit qu'en moyenne, sur de nombreuses itérations, l'estimation converge vers le vrai gradient.

### 8.3 Résultat : définition de P\*, I\*, D\*

À la convergence de l'algorithme, on note **P\*, I\*, D\*** les valeurs optimales trouvées par SPSA. L'étoile (\*) est la notation mathématique standard désignant un optimum — le point qui minimise la loss function sur l'ensemble des épisodes de test.

| Paramètre optimal | Signification physique |
|---|---|
| P\* | Gain proportionnel optimal : réactivité de la correction instantanée à l'erreur |
| I\* | Gain intégral optimal : capacité à éliminer l'erreur statique résiduelle |
| D\* | Gain dérivé optimal : anticipation des variations rapides, amortissement des oscillations |

Ces trois valeurs constituent le réglage PID définitif à charger sur le Teensy pour le comportement en course. Elles sont spécifiques à la configuration testée (banc ou piste) et à la loss function utilisée lors de l'optimisation.

---

## 9. Simulation — Complément au Plan SPSA

> 📍 **Contexte : Simulation uniquement** — cette section décrit le robot virtuel. Le mode réel (model-free) est le déploiement final vers lequel la simulation prépare le transfert.

La simulation est un outil de développement et de validation, **non un substitut au système réel**. Son rôle est de permettre de déboguer l'algorithme SPSA, de vérifier la cohérence des paramètres et d'obtenir un warm start avant de transférer sur le robot physique. SPSA tournera sur le robot réel ; la simulation prépare ce transfert.

### 9.1 Architecture du simulateur

Le simulateur reproduit la chaîne physique complète. L'inductance L est négligée en régime quasi-statique (dynamique électrique très rapide devant la mécanique), ce qui réduit le modèle à deux équations :

```python
i(t)    ≈ (V_pwm - Ke·ω) / R               # courant quasi-statique
dω/dt    = (Kt·i - B·ω - Tf) / J_total    # dynamique mécanique
V_pwm    = duty × V_bat - V_drop_IBT2      # tension effective après pont H
```

### 9.2 Interface d'abstraction robot/simulation

Le code sera structuré autour d'une interface commune qui permet de substituer le simulateur par le robot réel sans modifier l'algorithme SPSA. Cette séparation est la clé du transfert *sim-to-real* :

```python
class MotorInterface:
    def run_episode(P, I, D) -> loss:
        # SimulatedMotor  : intègre le modèle ODE sur dt
        # RealMotor       : envoie PWM Teensy, lit odométrie Hall
```

### 9.3 Ordre d'implémentation

1. Modèle physique seul — vérifier la step response sur les deux vitesses cibles
2. Boucle PID autour du modèle — vérifier la stabilité et la convergence
3. Intégration SPSA sur la simulation — obtenir P\*, I\*, D\* simulés
4. Ajout du télémètre simulé et freinage — optimiser `d_seuil`
5. Transfert sur robot réel avec P\*, I\*, D\* simulés comme warm start SPSA

---

## 10. Prochaines Étapes

| Priorité | Action | Prérequis |
|---|---|---|
| 1 | Mesurer G (rapport de transmission) sur le robot | Accès au robot |
| 2 | Mesurer R à l'ohmmètre | Multimètre |
| 3 | Coder et valider le modèle physique (simulation) | — |
| 4 | Brancher SPSA sur la simulation | Étape 3 |
| 5 | Tester le freinage dynamique IBT-2 sur banc | Accès au robot |
| 6 | Mesurer la distance de freinage réelle | Étapes 3+5 |
| 7 | Transfert sur robot réel | Toutes précédentes |

---

## Annexe — Paramètres de Simulation par Défaut

Ces valeurs sont des estimations typiques pour un moteur DC brushed RC sur 2S. Elles serviront de point de départ pour la simulation avant toute identification expérimentale. Toutes sont ajustables dans le code.

| Paramètre | Valeur | Unité |
|---|---|---|
| R — résistance armature | 1.0 | Ω |
| L — inductance | 0.5 × 10⁻³ | H |
| Ke — constante fcem | 0.03 | V·s/rad |
| Kt — constante de couple | 0.03 | N·m/A |
| J — inertie totale vue roue | 0.0013 | kg·m² |
| B — frottement visqueux | 0.005 | — |
| Tf — frottement sec | 0.02 | N·m |
| G — rapport de transmission | 10 *(information manquante)* | — |
| V_bat — tension batterie | 7.4 | V |
| r — rayon roue | 0.036 | m |
| M — masse véhicule | 1.0 | kg |