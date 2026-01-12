#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// WiFi
const char* ssid = "iPhone";
//const char* password = "ITetudes.256";
const char* password = "cedrixazerti";
// MQTT
const char* broker = "172.20.10.5";
int port = 1883;

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);


void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Démarrage...");
  
  // I2C et PWM
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(60);
  Serial.println("PWM initialisé");
  
  // WiFi
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);
  
  // Attendre connexion ET adresse IP valide
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  //  AUGMENTER LE BUFFER MQTT 
  mqttClient.setKeepAliveInterval(60000);
  mqttClient.setConnectionTimeout(5000);
  
  // MQTT
  Serial.print("Connexion MQTT...");
  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT erreur: ");
    Serial.println(mqttClient.connectError());
    while (1);
  }
  
  // S'abonner avec QoS 0 (pas de buffer)
  mqttClient.subscribe("jambe_G", 0);
  Serial.println("Abonné à jambe_G");
}



void loop() {
  //  Compteur de messages
  static int msgCount = 0;
  
  static unsigned long lastReport = 0;
  
  mqttClient.poll();
  
  // Vérifier les messages
  int messageSize = mqttClient.parseMessage();
  if (messageSize) {
    msgCount++;
    
    String message = "";
    message.reserve(50);  // Préallouer
    
    while (mqttClient.available()) {
      message += (char)mqttClient.read();
    }
    Serial.println(message);
    // Parser
    int idx1 = message.indexOf(',');
    int idx2 = message.indexOf(',', idx1 + 1);
    
    if (idx1 > 0 && idx2 > idx1) {
      float theta1 = message.substring(0, idx1).toFloat();
      float theta2 = message.substring(idx1 + 1, idx2).toFloat();
      float theta3 = message.substring(idx2 + 1).toFloat();
      
      // Map et envoyer directement
      pwm.writeMicroseconds(0, int(map(theta1, 135, -135, 500, 2500)));
      pwm.writeMicroseconds(1, int(map(theta2, 135, -135, 500, 2500)));
      pwm.writeMicroseconds(2, int(map(theta3, 135, -135, 500, 2500)));
    }
  }
  
  // Afficher stats toutes les secondes
  if (millis() - lastReport >= 1000) {
    Serial.print("Messages/sec: ");
    Serial.println(msgCount);
    msgCount = 0;
    lastReport = millis();
  }
  
  // ✅ PAS DE DELAY ICI !
}


