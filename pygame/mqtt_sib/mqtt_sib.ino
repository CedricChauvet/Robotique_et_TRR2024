#include <WiFiS3.h>
#include <ArduinoMqttClient.h>

// WiFi
const char* ssid = "Bbox-BFE7AC14";
const char* password = "ITetudes.256";

// MQTT
const char* broker = "192.168.1.192";
int port = 1883;

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

void setup() {
  Serial.begin(115200);
  
  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi OK");
  
  // MQTT
  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT erreur: ");
    Serial.println(mqttClient.connectError());
    while (1);
  }
  Serial.println("MQTT OK");
  
  // S'abonner
  mqttClient.subscribe("jambe_G");
}

void loop() {
  mqttClient.poll();
  
  int messageSize = mqttClient.parseMessage();
  if (messageSize) {
    String message = "";
    
    while (mqttClient.available()) {
      message += (char)mqttClient.read();
    }
    
    // Parser "45.2,90.5,-12.3"
    int idx1 = message.indexOf(',');
    int idx2 = message.indexOf(',', idx1 + 1);
    
    float theta1 = message.substring(0, idx1).toFloat();
    float theta2 = message.substring(idx1 + 1, idx2).toFloat();
    float theta3 = message.substring(idx2 + 1).toFloat();
    

    Serial.println(message);
    // Format pour Serial Plotter
    //Serial.print("Theta1:");
    //Serial.print(theta1);
    //Serial.print("; Theta2:");
    //Serial.print(theta2);
    //Serial.print("; Theta3:");
    //Serial.println(theta3);
  }
}