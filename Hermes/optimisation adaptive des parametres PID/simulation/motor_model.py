# =============================================================
#  motor_model.py
#  Simulation moteur DC brushed — configuration banc
#  Equations electriques et mecaniques couplees
# =============================================================

class MotorModel:

    def __init__(self, config="banc"):

        # --- Electrique ---
        self.R    = 0.1      # Ω  resistance armature
        self.L    = 0.5e-3    # H  inductance (negligee en quasi-statique)
        self.Ke = 0.005    # V.s/rad  — cohérent avec KV ≈ 2000 RPM/V
        self.Kt = 0.005    # N.m/A    — toujours égal à Ke en SI
        self.G  = 5.0     # rapport de transmission typique RC

        # --- Mecanique banc ---
        self.r    = 0.036     # m  rayon roue
        self.J_B    = 0.0013    # kg.m²  inertie roues seules (sans masse vehicule)
        self.Tf = 0.00005   # N.m  frottement sec — réduit pour banc sans charge
        self.B  = 0.00005   # frottement visqueux — idem
        self.a_frein_B = 2  # m/s²  — à remplacer par la valeur du .ino

        # --- Mecanique piste ---
        self.M         = 1.0      # kg  masse vehicule
        self.J_P       = self.J_B + self.M * self.r ** 2   # kg.m²  banc + M*r²
        self.a_frein_P = 1.0      # m/s²   a remplacer par valeur .ino piste

        # --- Alimentation ---
        self.V_bat = 7.4      # V  LiPo 2S nominal

        # --- Etat interne ---
        self.i        = 0.0   # A   courant armature
        self.omega    = 0.0   # rad/s  vitesse angulaire roue
        self.cum_dist = 0.0   # m   distance cumulee

        # --- Configuration active ---
        self.set_config(config)
 

    def set_config(self, config):
        """Bascule entre configuration banc et piste"""
        if config == "banc":
            self.J       = self.J_B
            self.a_frein = self.a_frein_B
        elif config == "piste":
            self.J       = self.J_P
            self.a_frein = self.a_frein_P
        else:
            raise ValueError(f"config doit etre 'banc' ou 'piste', recu : {config}")
        self.config = config

    def reset(self):
        self.i        = 0.0
        self.omega    = 0.0
        self.cum_dist = 0.0

    def step(self, duty, dt):
        """
        Integre un pas de temps dt (secondes) avec commande duty in [-1, 1]
        duty > 0 : avancer
        duty = 0 : frein dynamique (RPWM=0, LPWM=0, EN actifs)
        """
        if duty == 0.0:
            # freinage dynamique — decelereration issue de la mesure reelle
            domega_dt = -self.a_frein / self.r
        else:
            # Tension effective apres pont H
            V_pwm = duty * self.V_bat

            # Vitesse moteur (cote moteur, pas roue)
            omega_moteur = self.omega * self.G

            # --- Equation electrique (quasi-statique : L negligee) ---
            # V = R*i + Ke*omega_moteur  =>  i = (V - Ke*omega) / R
            self.i = (V_pwm - self.Ke * omega_moteur) / self.R

            # --- Equation mecanique ---
            # J * dω/dt = Kt*i/G - B*ω - Tf*sign(ω)
            couple_moteur  = self.Kt * self.i / self.G
            frot_visqueux  = self.B * self.omega
            frot_sec       = self.Tf * (1.0 if self.omega > 0 else -1.0)

            domega_dt = (couple_moteur - frot_visqueux - frot_sec) / self.J
        self.omega    += domega_dt * dt
        self.omega     = max(0.0, self.omega)   # pas de vitesse negative sur banc

        # --- Distance cumulee ---
        self.cum_dist += self.omega * self.r * dt

    def get_vitesse_kmh(self):
        return self.omega * self.r * 3.6

    def get_cum_dist(self):
        return self.cum_dist