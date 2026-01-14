#include <WiFi.h>  // ✅ Bibliothèque native ESP32
#include <PubSubClient.h>  // ✅ Meilleure bibliothèque MQTT
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
PubSubClient mqttClient(wifiClient);

float theta1 = 0;
float theta2 = 0;
float theta3 = 0;

// Throttling
unsigned long lastPWMUpdate = 0;
const unsigned long PWM_UPDATE_INTERVAL = 20;

// Watchdog I2C
unsigned long lastI2CCheck = 0;
const unsigned long I2C_CHECK_INTERVAL = 5000;
int i2cErrorCount = 0;

// ✅ Callback MQTT - appelé automatiquement à la réception
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  message.reserve(50);
  
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  // Parser
  int idx1 = message.indexOf(',');
  int idx2 = message.indexOf(',', idx1 + 1);
  
  if (idx1 > 0 && idx2 > idx1) {
    theta1 = message.substring(0, idx1).toFloat();
    theta2 = message.substring(idx1 + 1, idx2).toFloat();
    theta3 = message.substring(idx2 + 1).toFloat();
    
    Serial.printf("Angles: %.1f, %.1f, %.1f\n", theta1, theta2, theta3);
  }
}

bool checkI2C() {
  Wire.beginTransmission(0x40);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    Serial.printf("❌ Erreur I2C: %d\n", error);
    i2cErrorCount++;
    return false;
  }
  
  i2cErrorCount = 0;
  return true;
}

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

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connexion MQTT...");
    
    if (mqttClient.connect("ESP32_JambeG")) {
      Serial.println("✅ Connecté");
      mqttClient.subscribe("jambe_G");
    } else {
      Serial.printf("❌ Erreur : %d\n", mqttClient.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🚀 Démarrage ESP32...");
  
  // I2C
  Wire.begin(21, 22);  // SDA=21, SCL=22 (pins par défaut ESP32)
  Wire.setClock(100000);
  pwm.begin();
  pwm.setPWMFreq(60);
  
  if (checkI2C()) {
    Serial.println("✅ PWM initialisé");
  } else {
    Serial.println("❌ Erreur init PWM");
    resetI2C();
  }
  
  // WiFi avec auto-reconnect
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  
  Serial.printf("Connexion WiFi à %s", ssid);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connecté");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n❌ WiFi timeout - redémarrage...");
    ESP.restart();
  }
  
  // MQTT
  mqttClient.setServer(broker, port);
  mqttClient.setCallback(callback);
  mqttClient.setKeepAlive(60);
  mqttClient.setSocketTimeout(5);
  
  // ✅ Buffer MQTT agrandi (important !)
  mqttClient.setBufferSize(512);
  
  reconnectMQTT();
}

void loop() {
  static int msgCount = 0;
  static unsigned long lastReport = 0;
  
  
  // Auto-reconnect MQTT
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  
  // ✅ PubSubClient gère mieux le buffer automatiquement
  mqttClient.loop();
  
  // Watchdog I2C
  if (millis() - lastI2CCheck >= I2C_CHECK_INTERVAL) {
    if (!checkI2C()) {
      Serial.println("⚠️ Problème I2C détecté");
      if (i2cErrorCount >= 3) {
        resetI2C();
      }
    }
    lastI2CCheck = millis();
  }
  
  // Update servos throttlé
    Wire.beginTransmission(0x40);
    if (Wire.endTransmission() == 0) {
      int ms1 = constrain(map(theta1, -135, 135, 500, 2500), 500, 2500);
      int ms2 = constrain(map(theta2, -135, 135, 500, 2500), 500, 2500);
      int ms3 = constrain(map(theta3, -135, 135, 500, 2500), 500, 2500);
      
      pwm.writeMicroseconds(0, ms1);
      pwm.writeMicroseconds(1, ms2);
      pwm.writeMicroseconds(2, ms3);
    }
    
    lastPWMUpdate = millis();
    delay(5);
  
}