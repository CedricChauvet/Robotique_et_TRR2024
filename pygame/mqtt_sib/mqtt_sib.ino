#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// WiFi
const char* ssid = "Bbox-BFE7AC14";
const char* password = "ITetudes.256";

// MQTT
const char* broker = "192.168.1.192";
int port = 1883;

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

float theta1 = 0;
float theta2 = 0;
float theta3 = 0;

// Variables pour throttling
unsigned long lastPWMUpdate = 0;
//const unsigned long PWM_UPDATE_INTERVAL = 20; // 50Hz max pour les servos

// Variables pour watchdog I2C
unsigned long lastI2CCheck = 0;
const unsigned long I2C_CHECK_INTERVAL = 5000;
int i2cErrorCount = 0;

// ✅ Fonction pour vérifier la santé I2C
bool checkI2C() {
  Wire.beginTransmission(0x40);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    Serial.print("❌ Erreur I2C: ");
    Serial.println(error);
    i2cErrorCount++;
    return false;
  }
  
  i2cErrorCount = 0;
  return true;
}

// ✅ Réinitialiser I2C en cas d'erreur
void resetI2C() {
  Serial.println("🔄 Réinitialisation I2C...");
  
  Wire.end();
  delay(100);
  
  Wire.begin();
  delay(100);
  
  pwm.begin();
  pwm.setPWMFreq(60);
  delay(100);
  
  Serial.println("✅ I2C réinitialisé");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Démarrage...");
  
  // I2C avec vérification
  Wire.begin();
  Wire.setClock(100000); // ✅ Réduire la vitesse I2C pour plus de fiabilité
  pwm.begin();
  pwm.setPWMFreq(60);
  
  if (checkI2C()) {
    Serial.println("✅ PWM initialisé");
  } else {
    Serial.println("❌ Erreur init PWM");
    resetI2C();
  }
  
  // WiFi
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connecté");
  
  // MQTT
  mqttClient.setKeepAliveInterval(60000);
  mqttClient.setConnectionTimeout(5000);
  
  Serial.print("Connexion MQTT...");
  if (!mqttClient.connect(broker, port)) {
    Serial.print("❌ MQTT erreur: ");
    Serial.println(mqttClient.connectError());
    while (1);
  }
  
  mqttClient.subscribe("jambe_G", 0);
  Serial.println("✅ Abonné à jambe_G");
}

void loop() {
  static int msgCount = 0;
  static unsigned long lastReport = 0;
  
  // ✅ Vérifier périodiquement la santé I2C
  if (millis() - lastI2CCheck >= I2C_CHECK_INTERVAL) {
    if (!checkI2C()) {
      Serial.println("⚠️ Problème I2C détecté");
      if (i2cErrorCount >= 3) {
        resetI2C();
      }
    }
    lastI2CCheck = millis();
  }
  
  mqttClient.poll();
  
  // Recevoir messages
  int messageSize = mqttClient.parseMessage();
  if (messageSize) {
    msgCount++;
    
    String message = "";
    message.reserve(50);
    
    while (mqttClient.available()) {
      message += (char)mqttClient.read();
    }
    
    // Parser
    int idx1 = message.indexOf(',');
    int idx2 = message.indexOf(',', idx1 + 1);
    
    if (idx1 > 0 && idx2 > idx1) {
      theta1 = message.substring(0, idx1).toFloat();
      theta2 = message.substring(idx1 + 1, idx2).toFloat();
      theta3 = message.substring(idx2 + 1).toFloat();
      
      Serial.print("Angles: ");
      Serial.print(theta1);
      Serial.print(", ");
      Serial.print(theta2);
      Serial.print(", ");
      Serial.println(theta3);
    }
  }
  
  // ✅ THROTTLING: Mettre à jour PWM seulement toutes les 20ms
  
    
    // Vérification rapide I2C avant d'écrire
    Wire.beginTransmission(0x40);
    if (Wire.endTransmission() == 0) {
      
      int ms1 = constrain(map(theta1, -135, 135, 500, 2500), 500, 2500);
      
      pwm.writeMicroseconds(0, 1500);
      pwm.writeMicroseconds(1, ms1);
      pwm.writeMicroseconds(2, 1500);
      
    } else {
      Serial.println("⚠️ Skip PWM - I2C occupé");
    }
    
    lastPWMUpdate = millis();
    delay(20);
  
  
  // Stats
  if (millis() - lastReport >= 1000) {
    Serial.print("Messages/sec: ");
    Serial.print(msgCount);
    Serial.print(" | I2C errors: ");
    Serial.println(i2cErrorCount);
    msgCount = 0;
    lastReport = millis();
  }
}