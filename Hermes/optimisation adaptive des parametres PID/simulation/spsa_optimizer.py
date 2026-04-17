# =============================================================
#  spsa_optimizer.py
#  Optimisation des parametres PID par algorithme SPSA
#  sur simulation MotorModel
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
from motor_model import MotorModel


DT = 1.0 / 100.0   #    100 Hz — identique au loop Teensy

# =============================================================
#  PID Controller
# =============================================================
class PIDController:
    def __init__(self, P, I, D):
        self.P = P
        self.I = I
        self.D = D
        self.integral      = 0.0
        self.last_error    = 0.0
        self.duty_filtre   = 0.0    # ← sortie filtrée

    def reset(self, integral_init=0.0, duty_init=1.0):
        self.last_error    = 0.0
        self.duty_filtre   = duty_init    # ← démarre à 1.0
        self.integral      = integral_init

    def compute(self, consigne, mesure, dt):
        error          = consigne - mesure
        self.integral += error * dt
        self.integral  = max(-5.0, min(5.0, self.integral))
        derivee        = (error - self.last_error) / dt if dt > 0 else 0.0
        self.last_error = error

        output = self.P * error + self.I * self.integral + self.D * derivee
        output = max(0.0, min(1.0, output))

        # filtre passe-bas — tau = constante de temps du filtre
        tau              = 0.05   # 50ms — à ajuster si trop lent
        alpha            = dt / (tau + dt)
        self.duty_filtre = alpha * output + (1.0 - alpha) * self.duty_filtre

        return self.duty_filtre
# =============================================================
#  Episode de simulation
# =============================================================


def run_episode(P, I, D, motor, consigne_kmh=8.0,
                duree=4.0, dt=DT):
    """
    Simule un episode de maintien de vitesse
    Retourne la loss ITAE
    """
    
  
 

    motor.reset()

    pid = PIDController(P, I, D)
    pid.reset()

    loss = 0.0
    n_steps = int(duree / dt)

    for n in range(n_steps):
        t       = n * dt
        mesure  = motor.get_vitesse_kmh()
        duty    = pid.compute(consigne_kmh, mesure, dt)
        motor.step(duty, dt)

        # ITAE — pénalise les erreurs qui persistent dans le temps
        erreur  = abs(consigne_kmh - mesure)
        loss   += t * erreur * dt

    return loss


# =============================================================
#  Algorithme SPSA
# =============================================================
def spsa(motor, consigne_kmh=8.0,
         n_iterations=100, alpha=0.1, c=0.1):
    """
    Optimise P, I, D par SPSA
    Retourne P*, I*, D* et l'historique de la loss
    """

    # --- Initialisation theta = [P, I, D] ---------------------
    theta = np.array([1.0, 0.1, 0.01])

    historique_loss  = []
    historique_theta = []

    print("=" * 50)
    print(f"  SPSA — config:{motor.config}  consigne:{consigne_kmh} km/h")
    print(f"  iterations:{n_iterations}  alpha:{alpha}  c:{c}")
    print("=" * 50)
    print(f"  {'iter':>5}  {'P':>8}  {'I':>8}  {'D':>8}  {'loss':>10}")
    print("-" * 50)

    for k in range(n_iterations):

        # decroissance de alpha et c
        ak = alpha / (k + 1) ** 0.602
        ck = c     / (k + 1) ** 0.101

        # perturbation aleatoire Delta = vecteur de ±1
        delta = np.random.choice([-1.0, 1.0], size=3)

        theta_plus  = theta + ck * delta
        theta_minus = theta - ck * delta

        # projection — pas de valeurs negatives
        theta_plus  = np.maximum(theta_plus,  [0.0, 0.0, 0.0])
        theta_minus = np.maximum(theta_minus, [0.0, 0.0, 0.0])

        # deux evaluations de la loss
        loss_plus  = run_episode(*theta_plus,  motor, consigne_kmh)
        loss_minus = run_episode(*theta_minus, motor, consigne_kmh)

        # estimation du gradient
        gradient = (loss_plus - loss_minus) / (2.0 * ck * delta)

        # mise a jour theta
        theta = theta - ak * gradient
        theta = np.maximum(theta, [0.0, 0.0, 0.0])   # projection ≥ 0

        # loss courante
        loss_courante = run_episode(*theta, motor, consigne_kmh)
        historique_loss.append(loss_courante)
        historique_theta.append(theta.copy())

        if k % 10 == 0:
            print(f"  {k:>5}  {theta[0]:>8.4f}  {theta[1]:>8.4f}"
                  f"  {theta[2]:>8.4f}  {loss_courante:>10.4f}")

    print("=" * 50)
    print(f"  P* = {theta[0]:.4f}")
    print(f"  I* = {theta[1]:.4f}")
    print(f"  D* = {theta[2]:.4f}")
    print(f"  loss finale = {historique_loss[-1]:.4f}")
    print("=" * 50)

    return theta, historique_loss, historique_theta


# =============================================================
#  Visualisation des resultats
# =============================================================
def plot_resultats(theta_star, motor, consigne_kmh,
                   historique_loss):

    P, I, D = theta_star

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # --- Graphe 1 : convergence de la loss ---
    axes[0].plot(historique_loss, color='steelblue', linewidth=1.2)
    axes[0].set_xlabel("iteration")
    axes[0].set_ylabel("loss ITAE")
    axes[0].set_title("Convergence SPSA")
    axes[0].grid(True, alpha=0.3)

    # --- Graphe 2 : step response avec P*, I*, D* ---
    motor.reset()
    pid = PIDController(P, I, D)
    pid.reset()

    dt, duree = 0.01, 5.0
    temps, vitesses, duties = [], [], []

    for n in range(int(duree / dt)):
        t      = n * dt
        mesure = motor.get_vitesse_kmh()
        duty   = pid.compute(consigne_kmh, mesure, dt)
        motor.step(duty, dt)
        temps.append(t)
        vitesses.append(mesure)
        duties.append(duty)

    axes[1].plot(temps, vitesses, color='steelblue',
                 linewidth=1.2, label='vitesse simulee')
    axes[1].axhline(y=consigne_kmh, color='red', linestyle='--',
                    linewidth=1, label=f'consigne {consigne_kmh} km/h')
    axes[1].set_xlabel("temps (s)")
    axes[1].set_ylabel("vitesse (km/h)")
    axes[1].set_title(f"Step response — P*={P:.3f} I*={I:.3f} D*={D:.3f}")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    # --- Graphe 3 : commande duty ---
    axes[2].plot(temps, duties, color='darkorange',
                 linewidth=1.0, label='duty PID')
    axes[2].axhline(y=0, color='gray', linewidth=0.5)
    axes[2].set_xlabel("temps (s)")
    axes[2].set_ylabel("duty [-1, 1]")
    axes[2].set_title("Commande PWM")
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.3)

    plt.suptitle(f"SPSA — config:{motor.config}  consigne:{consigne_kmh} km/h",
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(f"spsa_result_{motor.config}_{int(consigne_kmh)}kmh.png", dpi=150)
    plt.show()


# =============================================================
#  Main
# =============================================================
if __name__ == "__main__":

    motor = MotorModel(config="banc")

    # Optimisation sur maintien 8 km/h
    theta_star, historique_loss, _ = spsa(
        motor,
        consigne_kmh  = 8.0,
        n_iterations  = 500,
        alpha         = 0.1,
        c             = 0.1
    )

    plot_resultats(theta_star, motor,
                   consigne_kmh   = 8.0,
                   historique_loss = historique_loss,
                   )