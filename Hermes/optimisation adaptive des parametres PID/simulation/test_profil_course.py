# =============================================================
#  test_profil_course.py
#  Simulation d'un profil de course complet
#  0 → 14 km/h (10m) → 8 km/h (10m) → 14 km/h (10m)
#  Utilise les P*, I*, D* trouvés par SPSA
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
from motor_model import MotorModel
from spsa_optimizer import PIDController, DT

# =============================================================
#  Paramètres du profil
# =============================================================
DIST_LIGNE   = 10.0   # m — ligne droite à 14 km/h
DIST_VIRAGE  = 10.0   # m — virage à 8 km/h
VIT_LIGNE    = 14.0   # km/h
VIT_VIRAGE   =  8.0   # km/h

# P*, I*, D* issus de SPSA — à remplacer par vos valeurs
# Exemple avec config banc :
P_STAR = 3.1209
I_STAR = 0.0535
D_STAR = 0.0314



# =============================================================
#  Générateur de consigne basé sur la distance
# =============================================================
def get_consigne(dist):
    """
    Retourne la consigne de vitesse selon la distance parcourue
    Segment 1 : 0   → 10m   → 14 km/h
    Segment 2 : 10m → 20m   →  8 km/h
    Segment 3 : 20m → 30m   → 14 km/h
    """
    if dist < DIST_LIGNE:
        return VIT_LIGNE
    elif dist < DIST_LIGNE + DIST_VIRAGE:
        return VIT_VIRAGE
    else:
        return VIT_LIGNE

# =============================================================
#  Simulation du profil complet
# =============================================================
def simuler_profil(P, I, D, motor, dt=DT):

    motor.reset()
    pid = PIDController(P, I, D)
    pid.reset(duty_init=1.0)

    dist_max = DIST_LIGNE + DIST_VIRAGE + DIST_LIGNE

    temps      = []
    vitesses   = []
    consignes  = []
    duties     = []
    distances  = []

    t = 0.0

    while motor.get_cum_dist() < dist_max:

        dist     = motor.get_cum_dist()
        mesure   = motor.get_vitesse_kmh()
        consigne = get_consigne(dist)

        duty = pid.compute(consigne, mesure, dt)
        motor.step(duty, dt)

        temps.append(t)
        vitesses.append(mesure)
        consignes.append(consigne)
        duties.append(duty)
        distances.append(dist)

        t += dt

        # sécurité — timeout 60s
        if t > 60.0:
            print("# TIMEOUT — simulation trop longue")
            break

    return temps, vitesses, consignes, duties, distances

# =============================================================
#  Visualisation
# =============================================================
def plot_profil(temps, vitesses, consignes, duties, distances, config):

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=False)

    # --- Graphe 1 : vitesse vs temps ---
    axes[0].plot(temps, vitesses,  color='steelblue',  linewidth=1.5,
                 label='vitesse simulee')
    axes[0].plot(temps, consignes, color='red',        linewidth=1.0,
                 linestyle='--', label='consigne')
    axes[0].axhline(y=VIT_LIGNE,  color='green', linestyle=':', linewidth=0.8)
    axes[0].axhline(y=VIT_VIRAGE, color='orange', linestyle=':', linewidth=0.8)
    axes[0].set_ylabel("vitesse (km/h)")
    axes[0].set_xlabel("temps (s)")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title(f"Vitesse vs temps — config:{config}")

    # --- Graphe 2 : vitesse vs distance ---
    axes[1].plot(distances, vitesses,  color='steelblue', linewidth=1.5,
                 label='vitesse simulee')
    axes[1].plot(distances, consignes, color='red',       linewidth=1.0,
                 linestyle='--', label='consigne')

    # zones colorées
    axes[1].axvspan(0,                          DIST_LIGNE,
                    alpha=0.05, color='green',  label='ligne droite')
    axes[1].axvspan(DIST_LIGNE,                 DIST_LIGNE + DIST_VIRAGE,
                    alpha=0.05, color='orange', label='virage')
    axes[1].axvspan(DIST_LIGNE + DIST_VIRAGE,   DIST_LIGNE*2 + DIST_VIRAGE,
                    alpha=0.05, color='green')

    axes[1].set_ylabel("vitesse (km/h)")
    axes[1].set_xlabel("distance (m)")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title("Vitesse vs distance")

    # --- Graphe 3 : commande PWM vs temps ---
    axes[2].plot(temps, duties, color='darkorange', linewidth=1.0,
                 label='duty PID')
    axes[2].axhline(y=0, color='gray', linewidth=0.5)
    axes[2].set_ylabel("duty [0, 1]")
    axes[2].set_xlabel("temps (s)")
    axes[2].legend(fontsize=9)
    axes[2].grid(True, alpha=0.3)
    axes[2].set_title("Commande PWM")

    plt.suptitle(
        f"Profil course — config:{config}  "
        f"P*={P_STAR}  I*={I_STAR}  D*={D_STAR}",
        fontsize=11)
    plt.tight_layout()
    plt.savefig(f"profil_course_{config}.png", dpi=150)
    plt.show()

# =============================================================
#  Résultats console
# =============================================================
def afficher_resultats(temps, vitesses, consignes, distances):

    # Trouver le moment où on entre dans le virage
    idx_virage = next(i for i, d in enumerate(distances)
                      if d >= DIST_LIGNE)
    # Trouver le moment où on sort du virage
    idx_sortie = next(i for i, d in enumerate(distances)
                      if d >= DIST_LIGNE + DIST_VIRAGE)

    vit_entree_virage = vitesses[idx_virage]
    t_total           = temps[-1]

    # Erreur moyenne en virage
    erreur_virage = np.mean([abs(consignes[i] - vitesses[i])
                             for i in range(idx_virage, idx_sortie)])

    print("=" * 45)
    print("  RESULTATS PROFIL COURSE")
    print("=" * 45)
    print(f"  Temps total          : {t_total:.2f} s")
    print(f"  Vitesse entrée virage: {vit_entree_virage:.2f} km/h")
    print(f"  Erreur moy. virage   : {erreur_virage:.3f} km/h")
    print(f"  Distance totale      : {distances[-1]:.2f} m")
    print("=" * 45)

# =============================================================
#  Main
# =============================================================
if __name__ == "__main__":

    config = "banc"   # ← changer ici pour "piste"
    motor  = MotorModel(config=config)

    temps, vitesses, consignes, duties, distances = simuler_profil(
        P_STAR, I_STAR, D_STAR, motor
    )

    afficher_resultats(temps, vitesses, consignes, distances)
    plot_profil(temps, vitesses, consignes, duties, distances, config)