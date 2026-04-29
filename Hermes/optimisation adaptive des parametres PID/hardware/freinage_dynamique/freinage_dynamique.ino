// =============================================================
//  freinage_caracterisation.ino
//  Teensy — IBT-2 — Capteur Hall odométrie
//
//  Objectif : mesurer la décélération en frein dynamique
//  lors d'une transition vitesse réelle → 8 km/h
//
//  Sortie Série MQTT : CSV  temps_ms;etat;mode;VIT;cumDist;nbPignon;nb_tour_sec;PWM
//  → exploiter dans freinage_caracterisation.py pour les graphes
// =============================================================

// ---- Broches IBT-2 ------------------------------------------
#define RPWM   11
#define LPWM   12
#define R_EN   7
#define L_EN   8

// ---- Broche odométrie Hall ----------------------------------
#define PIN_ODO  3    // broche interruption Teensy

// ---- Paramètres physiques -----------------------------------
const float DIAMETRE_ROUE_M  = 0.072;
const float PI_F              = 3.14159265;
const float PERIMETRE_ROUE_M  = PI_F * DIAMETRE_ROUE_M;  // ~0.2262 m

// ---- Consignes de vitesse -----------------------------------
const float VIT_BASSE        =  8.0;    // km/h — vitesse cible après freinage
const int   PWM_ACCEL        = 180;     // PWM pour atteindre la vitesse de départ (à ajuster)
const unsigned long DUREE_AVANT_FREIN = 4000;  // 3s accel + 1s stabilisation

// ---- Variables odométrie ------------------------------------
volatile unsigned long nbPignon = 0;

float VIT         = 0.0;   // km/h
float cumDist     = 0.0;   // m
float nb_tour_sec = 0.0;

// ---- Variables test -----------------------------------------
enum Mode { ATTENTE, ACCELERATION, FREINAGE };
Mode etatTest = ATTENTE;

String modeFreinage = "DYNAMIQUE";
// String modeFreinage = "COAST";   // décommenter pour le test coast
// String modeFreinage = "ACTIF";   // décommenter pour le test actif

unsigned long tDebut         = 0;
unsigned long tDebutFreinage = 0;
float distDebutFreinage      = 0.0;
float vitDebutFreinage       = 0.0;   // vitesse réelle mesurée au moment du freinage

// ---- Log ----------------------------------------------------
const int  LOG_INTERVAL_MS = 20;   // 50 Hz
unsigned long lastMsg      = 0;
bool logActif = false;
String chaine = "";

// =============================================================
void setup() {
  Serial.begin(115200);
  Serial6.begin(115200);

  while (!Serial || !Serial6) {}

  // IBT-2
  pinMode(RPWM, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_EN, OUTPUT);

  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);

  arreter();

  // Odométrie
  pinMode(PIN_ODO, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ODO), countInterrupt, FALLING);

  Serial.println("# freinage_caracterisation.ino pret");
  Serial.print("# Mode de freinage : "); Serial.println(modeFreinage);
  Serial.println("# temps_ms;etatTest;modeFreinage;VIT;cumDist;nbPignon;nb_tour_sec;PWM_ACCEL");

  nbPignon    = 0;
  cumDist     = 0.0;
  VIT         = 0.0;
  nb_tour_sec = 0.0;
  tDebut      = millis();
  logActif    = true;
  etatTest    = ACCELERATION;
  Serial.println("# Debut test");
}

// =============================================================
void loop() {

  compteur();

  switch (etatTest) {

    case ACCELERATION:
      avancer(PWM_ACCEL);
      if (millis() - tDebut >= DUREE_AVANT_FREIN) {
        tDebutFreinage    = millis();
        distDebutFreinage = cumDist;
        vitDebutFreinage  = VIT;     // vitesse réelle mesurée
        arreter();                   // IBT-2 maintient cet état jusqu'à la fin
        etatTest = FREINAGE;
      }
      break;
 case FREINAGE:
      if (millis() - tDebutFreinage > 10000) {
        Serial.println("# TIMEOUT — verifier odometrie");
        logActif = false;
        etatTest = ATTENTE;
        break;
      }
      if (VIT <= VIT_BASSE) {
        unsigned long duree_ms = millis() - tDebutFreinage;
        float dist_m           = cumDist - distDebutFreinage;
        float decel_mss        = vitesseKmhToMs(vitDebutFreinage - VIT_BASSE)
                                 / (duree_ms / 1000.0);

        Serial.println("# ---- RESULTATS ----");
        Serial.print("# Mode            : "); Serial.println(modeFreinage);
        Serial.print("# Vit. debut      : "); Serial.print(vitDebutFreinage, 2); Serial.println(" km/h");
        Serial.print("# Duree freinage  : "); Serial.print(duree_ms);            Serial.println(" ms");
        Serial.print("# Distance        : "); Serial.print(dist_m, 3);           Serial.println(" m");
        Serial.print("# Deceleration ~  : "); Serial.print(decel_mss, 2);        Serial.println(" m/s2");
        Serial.println("# --------------------");
        logActif = false;
        etatTest = ATTENTE;
      }
      break;


  case ATTENTE:
      // état terminal — IBT-2 en frein, moteur arrêté
      // rien à faire
      break;


  if (logActif) messageOut();
  }
}

// =============================================================
//  Odométrie
// =============================================================
void countInterrupt() {
  nbPignon++;
}

void compteur() {
  static unsigned long lastNb    = 0;
  static unsigned long lastMicro = 0;

  unsigned long nb    = nbPignon;
  unsigned long delta = nb - lastNb;

  if (delta > 0) {
    unsigned long now   = micros();
    unsigned long dt_us = now - lastMicro;

    if (dt_us > 0) {
      nb_tour_sec = (float)delta / (dt_us / 1000000.0);
      VIT         = nb_tour_sec * PERIMETRE_ROUE_M * 3600.0 * 2.0;   // km/h
      cumDist     = (float)nb  * PERIMETRE_ROUE_M * 2.0;             // m
    }

    lastNb    = nb;
    lastMicro = micros();
  }
}

// =============================================================
//  Commandes IBT-2
// =============================================================
void avancer(int pwm) {
  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
  analogWrite(RPWM, pwm);
  analogWrite(LPWM, 0);
}

void freinDynamique() {
  // Court-circuite les bornes moteur via les Low-Side FET
  // RPWM=0, LPWM=0 avec les enables actifs
  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);
}

void freinCoast() {
  // Freinage par friction — enables desactives
  digitalWrite(R_EN, LOW);
  digitalWrite(L_EN, LOW);
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);
}

void freinActif(int pwm=50) {
  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
  analogWrite(RPWM, 0);
  analogWrite(LPWM, pwm);
}


void arreter() {
  if (modeFreinage == "DYNAMIQUE") {
    freinDynamique();
  }
  else if (modeFreinage == "COAST") {
    freinCoast();
  }
  else if (modeFreinage == "ACTIF") {
    freinActif();
  }
}

// =============================================================
//  Utilitaires
// =============================================================
float vitesseKmhToMs(float kmh) {
  return kmh / 3.6;
}

// =============================================================
//  Log Serie
// =============================================================
void messageOut() {
  if (!logActif) return;
  if (millis() - lastMsg < LOG_INTERVAL_MS) return;
  lastMsg = millis();

  chaine  = String(millis() - tDebut) + ";";
  chaine += String(etatTest)          + ";";
  chaine += String(modeFreinage)      + ";";
  chaine += String(VIT)               + ";";
  chaine += String(cumDist)           + ";";
  chaine += String(nbPignon)          + ";";
  chaine += String(nb_tour_sec)       + ";";
  chaine += String(PWM_ACCEL)         + ";";

  Serial6.println(chaine);
}