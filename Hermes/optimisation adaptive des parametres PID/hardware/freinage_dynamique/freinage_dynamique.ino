// =============================================================
//  freinage_caracterisation.ino
//  Teensy — IBT-2 — Capteur Hall odométrie
//
//  Objectif : comparer la décélération en mode coast vs frein
//  dynamique lors d'une transition 14 km/h → 8 km/h
//

//  Sortie Série MQTT : CSV  temps_ms, vitesse_kmh, distance_m, mode
//  → coller dans freinage_caracterisation.py pour les graphes
// =============================================================

// ---- Broches IBT-2 ------------------------------------------
#define RPWM   11
#define LPWM   12
#define R_EN   7
#define L_EN   8

// ---- Broche odométrie Hall ----------------------------------
#define PIN_ODO  3    // doit être une broche interruption Teensy

// ---- Paramètres physiques -----------------------------------
const float DIAMETRE_ROUE_M = 0.072;          // 7.2 cm
const float PI_F             = 3.14159265;
const float PERIMETRE_ROUE_M = PI_F * DIAMETRE_ROUE_M;  // ~0.2262 m

// ---- Consignes de vitesse -----------------------------------
const float VIT_HAUTE   = 14.0;   // km/h — vitesse de départ
const float VIT_BASSE   =  8.0;   // km/h — vitesse cible après freinage
const int   PWM_ACCEL   = 180;    // PWM pour atteindre ~14 km/h (à ajuster)
const float TOLERANCE   =  0.5;   // km/h — fenêtre de stabilisation

// ---- Variables odométrie ------------------------------------
volatile unsigned long nbPignon    = 0;
volatile unsigned long lastNbPignon = 0;
volatile unsigned long lastMicro   = 0;

float VIT      = 0.0;   // km/h
float cumDist  = 0.0;   // m
float nb_tour_sec = 0.0;

// ---- Variables test -----------------------------------------
enum Mode { ATTENTE, ACCELERATION, STABILISATION, FREINAGE, TERMINE };
Mode etatTest = ATTENTE;

String modeFreinage = "DYNAMIQUE";
// String modeFreinage = "COAST"; dans le cas d'un ralentissement naturel
unsigned long tDebut        = 0;
unsigned long tDebutFreinage = 0;
float distDebutFreinage     = 0.0;


// ---- Durées des phases --------------------------------------
const unsigned long DUREE_ACCEL_MS   = 3000;   // 3s d'accélération
const unsigned long DUREE_STAB_MS    = 1000;   // 1s de stabilisation


// ---- Log ----------------------------------------------------
const int  LOG_INTERVAL_MS = 20;    // 50 Hz
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

  // Enables actifs par défaut
  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);

  arreter();

  // Odométrie
  pinMode(PIN_ODO, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ODO), countInterrupt, FALLING);

  Serial.println("# freinage_dynamique.ino pret");
  Serial.print("Mode de freinage: ");Serial.println(modeFreinage);
  nbPignon     = 0;
  cumDist      = 0.0;
  VIT          = 0.0;
  nb_tour_sec  = 0.0;
  tDebut       = millis();
  logActif     = true;
  etatTest     = ACCELERATION;
  Serial.println("# Debut test FREIN_DYNAMIQUE");
}

// =============================================================
void loop() {

  calculerVitesse();   // ← ajouter cette ligne ici
    
  // Machine à états temporelle
  switch (etatTest) {

    case ACCELERATION:
      avancer(PWM_ACCEL);
      if (millis() - tDebut >= DUREE_ACCEL_MS) {
        etatTest = STABILISATION;
      }
      break;

    case STABILISATION:
      avancer(PWM_ACCEL);
      if (millis() - tDebut >= DUREE_ACCEL_MS + DUREE_STAB_MS) {
        tDebutFreinage    = millis();
        distDebutFreinage = cumDist;
        freinDynamique();
        etatTest = FREINAGE;
      }
      break;

    case FREINAGE:
      if (VIT <= VIT_BASSE) {
        arreter();
        unsigned long duree_ms = millis() - tDebutFreinage;
        float dist_m           = cumDist - distDebutFreinage;
        float decel_mss        = vitesseKmhToMs(VIT_HAUTE - VIT_BASSE)
                                 / (duree_ms / 1000.0);

        Serial.println("# ---- RESULTATS ----");
        Serial.print("# Mode            : "); Serial.println(modeFreinage);
        Serial.print("# Duree freinage  : "); Serial.print(duree_ms);   Serial.println(" ms");
        Serial.print("# Distance        : "); Serial.print(dist_m, 3);  Serial.println(" m");
        Serial.print("# Deceleration ~  : "); Serial.print(decel_mss, 2); Serial.println(" m/s²");
        Serial.println("# --------------------");
        Serial.println("# Test terminé. Envoyer n'importe quelle touche pour relancer.");
        logActif = false;
        etatTest = ATTENTE;
      }
      break;

    default:
      break;
  }

  // Log série
  if (logActif) messageOut();
}

// =============================================================
//  Odométrie
// =============================================================
void countInterrupt() {
  nbPignon++;
}

void calculerVitesse() {
  static unsigned long lastNb    = 0;
  static unsigned long lastMicro = 0;

  unsigned long nb = nbPignon;
  unsigned long delta = nb - lastNb;

  if (delta > 0) {
    unsigned long now   = micros();
    unsigned long dt_us = now - lastMicro;

    if (dt_us > 0) {
      nb_tour_sec = (float)delta / (dt_us / 1000000.0);
      VIT         = nb_tour_sec * PERIMETRE_ROUE_M * 3600.0;   // km/h
      cumDist     = (float)nb * PERIMETRE_ROUE_M;              // m
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
  // freinage par friction moteur
  // RPWM=0, LPWM=0 avec les enables desactivés
  digitalWrite(R_EN, LOW);
  digitalWrite(L_EN, LOW);
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);
}


void arreter() {
  if (modeFreinage == "DYNAMIQUE") {
    freinDynamique();
  }
  else if (modeFreinage == "COAST") {
    freinCoast();
  }
}

// =============================================================
//  Utilitaires
// =============================================================
float vitesseKmhToMs(float kmh) {
  return kmh / 3.6;
}

// =============================================================
//  Log Série
// =============================================================
void messageOut() {
  if (!logActif) return;
  if (millis() - lastMsg < LOG_INTERVAL_MS) return;
  lastMsg = millis();

  chaine  = String(millis() - tDebut)  + ";";
  chaine += String(etatTest)           + ";";
  chaine += String(modeFreinage)       + ";";
  chaine += String(VIT)                + ";";
  chaine += String(cumDist)            + ";";
  chaine += String(nbPignon)           + ";";
  chaine += String(nb_tour_sec)        + ";";
  chaine += String(PWM_ACCEL)          + ";";

  Serial6.println(chaine);
  }
