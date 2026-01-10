#include <WiFiS3.h>
#include <ArduinoMqttClient.h>

// WiFi
const char* ssid = "Bbox-BFE7AC14";
const char* password = "ITetudes.256";

// MQTT
const char* broker = "192.168.1.86";  // LAPTOP
//const char* broker = "192.168.1.192";  // PC


int port = 1883;

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);


void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  // WiFi - Connexion
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);
  
  // Attendre connexion ET adresse IP valide
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connecté, attente IP...");
  
  // IMPORTANT : Attendre une IP valide
  while (WiFi.localIP() == IPAddress(0, 0, 0, 0)) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi OK !");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  
  // Le reste du code MQTT...
  mqttClient.setId("Arduino_Jambe_" + String(random(0xFFFF), HEX));
  mqttClient.setKeepAliveInterval(60000);
  mqttClient.setConnectionTimeout(5000);
  
  Serial.print("Connexion MQTT à ");
  Serial.print(broker);
  Serial.print(":");
  Serial.println(port);
  
  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT erreur code: ");
    Serial.println(mqttClient.connectError());
    while (1) delay(1000);
  }
  
  Serial.println("MQTT OK !");
  mqttClient.subscribe("jambe_G");
  Serial.println("Abonné à 'jambe_G'");
}



void loop() {
  // Maintenir la connexion MQTT
  mqttClient.poll();
  
  // Vérifier les messages
  int messageSize = mqttClient.parseMessage();
  if (messageSize) {
    String message = "";
    
    while (mqttClient.available()) {
      message += (char)mqttClient.read();
    }
    
    // Parser "45.2,90.5,-12.3"
    int idx1 = message.indexOf(',');
    int idx2 = message.indexOf(',', idx1 + 1);
    
    if (idx1 > 0 && idx2 > 0) {  // Vérification format
      float theta1 = message.substring(0, idx1).toFloat();
      float theta2 = message.substring(idx1 + 1, idx2).toFloat();
      float theta3 = message.substring(idx2 + 1).toFloat();
      
      Serial.print("Reçu: ");
      Serial.println(message);
      
      // Format pour Serial Plotter (décommenter si besoin)
      // Serial.print("Theta1:");
      // Serial.print(theta1);
      // Serial.print(",Theta2:");
      // Serial.print(theta2);
      // Serial.print(",Theta3:");
      // Serial.println(theta3);
    } else {
      Serial.println("Format message incorrect");
    }
  }
}