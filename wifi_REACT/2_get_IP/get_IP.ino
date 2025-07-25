#include <WiFiS3.h>

// Remplacez par vos identifiants WiFi
const char* ssid = "Bbox-BFE7AC14";
const char* password = "ITetudes.256";

void setup() {
  Serial.begin(115200);
  
  // Attendre l'ouverture du Serial Monitor
  while (!Serial) {
    delay(10);
  }
  
  Serial.println("=== CONNEXION WIFI ===");
  Serial.print("Tentative de connexion à: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("=== CONNEXION RÉUSSIE ===");
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
  Serial.print("Adresse IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Passerelle: ");
  Serial.println(WiFi.gatewayIP());
  Serial.print("Masque de sous-réseau: ");
  Serial.println(WiFi.subnetMask());
  Serial.print("Signal WiFi (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  Serial.println("=========================");
  Serial.println("Copiez l'adresse IP ci-dessus dans votre code React !");
}

void loop() {
  // Vérifier la connexion toutes les 30 secondes
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 30000) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("IP actuelle: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.println("Connexion WiFi perdue !");
    }
    lastCheck = millis();
  }
  
  delay(1000);
}