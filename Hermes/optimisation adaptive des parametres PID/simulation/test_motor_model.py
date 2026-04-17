# =============================================================
#  test_motor_model.py
#  Validation de la step response du modele moteur
#  avant de brancher SPSA
# =============================================================

import matplotlib.pyplot as plt
from motor_model import MotorModel

# --- Parametres simulation ------------------------------------
dt    = 0.001   # pas de temps 1 ms
t_max = 15.0     # duree totale 5 secondes

# --- Scenario ------------------------------------------------
#  0s  → 3s  : avancer duty=0.7  (montee vers vitesse stabilisee)
#  3s  → 4s  : frein dynamique duty=0.0
#  4s  → 5s  : repos

motor = MotorModel()
motor.reset()

temps     = []
vitesses  = []
distances = []
duties    = []

for n in range(int(t_max / dt)):
    t = n * dt

    if   t < 10.0:
        duty = 0.7
    else:
        duty = 0.0

    motor.step(duty, dt)

    temps.append(t)
    vitesses.append(motor.get_vitesse_kmh())
    distances.append(motor.get_cum_dist())
    duties.append(duty * 20)   # mis a l'echelle pour lisibilite sur le graphe

# --- Resultats console ----------------------------------------
vit_max = max(vitesses)
idx_frein = int(10.0 / dt)
vit_debut_frein = vitesses[idx_frein]

# chercher quand VIT passe sous 8 km/h apres le freinage
t_atteint_8 = None
for n in range(idx_frein, len(vitesses)):
    if vitesses[n] <= 8.0:
        t_atteint_8 = temps[n]
        break

print("=" * 40)
print("  RESULTATS STEP RESPONSE")
print("=" * 40)
print(f"  Vitesse max atteinte   : {vit_max:.2f} km/h")
print(f"  Vitesse au freinage    : {vit_debut_frein:.2f} km/h")
if t_atteint_8:
    duree_frein = t_atteint_8 - 10.0
    dist_frein  = distances[int(t_atteint_8 / dt)] - distances[idx_frein]
    decel       = (vit_debut_frein - 8.0) / 3.6 / duree_frein
    print(f"  Temps pour atteindre 8 km/h : {duree_frein*1000:.0f} ms")
    print(f"  Distance de freinage        : {dist_frein:.3f} m")
    print(f"  Deceleration moyenne        : {decel:.2f} m/s2")
else:
    print("  8 km/h non atteint dans la simulation")
print("=" * 40)

# --- Graphe ---------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

# Vitesse
ax1.plot(temps, vitesses, color='steelblue', linewidth=1.5, label='vitesse simulee')
ax1.plot(temps, duties,   color='gray',      linewidth=0.8,
         linestyle='--', alpha=0.6,          label='duty x20')
ax1.axhline(y=14.0, color='green',  linestyle=':', linewidth=1, label='14 km/h')
ax1.axhline(y=8.0,  color='red',    linestyle=':', linewidth=1, label='8 km/h')
ax1.axvline(x=10.0,  color='orange', linestyle='--', linewidth=1, label='debut frein')
ax1.set_ylabel("vitesse (km/h)")
ax1.legend(loc='upper right', fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.set_title(f"Step response — MotorModel banc  (G={motor.G}, duty=0.7)")

# Distance
ax2.plot(temps, distances, color='darkorange', linewidth=1.5)
ax2.axvline(x=10.0, color='orange', linestyle='--', linewidth=1)
ax2.set_ylabel("distance cumulee (m)")
ax2.set_xlabel("temps (s)")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("step_response.png", dpi=150)
plt.show()

print("  Graphe sauvegarde : step_response.png")