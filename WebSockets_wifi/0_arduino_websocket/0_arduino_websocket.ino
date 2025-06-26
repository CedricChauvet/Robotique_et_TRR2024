#include <WiFiS3.h>
#include <WebSocketsServer.h>

const char* ssid = "Bbox-BFE7AC14";
const char* password = "ITetudes.256";

WebSocketsServer webSocket = WebSocketsServer(81);

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.print("Client #");
            Serial.print(num);
            Serial.println(" déconnecté!");
            delay(2000);
            break;
            
        case WStype_CONNECTED:
            Serial.print("Client #");
            Serial.print(num);
            Serial.println(" connecté!");
            
            // Envoyer un message de bienvenue
            webSocket.sendTXT(num, "Connexion établie avec Arduino!");
            break;
        
        case WStype_TEXT:
            Serial.print("Message reçu du client #");
            Serial.print(num);
            Serial.print(": ");
            Serial.println((char*)payload);
            
            // Traiter les commandes
            if (strncmp((char*)payload, "setSpeed:", 9) == 0) {
                int speed = atoi((char*)payload + 9);
                Serial.print("Nouvelle vitesse reçue: ");
                Serial.println(speed);
                
                // Confirmer la réception
                String response = "Vitesse mise à jour: " + String(speed);
                webSocket.sendTXT(num, response);
            }
            break;
            
        default:
            break;
    }
}

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    // Connexion WiFi avec gestion d'IP
    WiFi.disconnect();
    delay(1000);
    
    Serial.println("=== CONNEXION WIFI ===");
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    
    Serial.println("\n✅ WiFi connecté!");
    
    // Attendre l'IP
    unsigned long start = millis();
    while (WiFi.localIP() == IPAddress(0, 0, 0, 0) && (millis() - start) < 10000) {
        delay(500);
        Serial.print("Attente IP...");
    }
    
    Serial.println();
    Serial.print("IP Arduino: ");
    Serial.println(WiFi.localIP());
    
    if (WiFi.localIP() != IPAddress(0, 0, 0, 0)) {
        // Démarrer le serveur WebSocket
        webSocket.begin();
        webSocket.onEvent(webSocketEvent);
        
        Serial.println("🚀 Serveur WebSocket démarré sur le port 81");
        Serial.print("URL pour React: ws://");
        Serial.print(WiFi.localIP());
        Serial.println(":81");
        Serial.println("=================================");
    } else {
        Serial.println("❌ Impossible de démarrer sans IP");
    }
}

void loop() {
    webSocket.loop();
    
    // Envoyer des données de capteur toutes les 2 secondes
    static unsigned long lastSensorSend = 0;
    if (millis() - lastSensorSend > 2000) {
        // Simuler une valeur de capteur (remplacez par votre vraie lecture)
        int sensorValue = random(0, 1024);
        String message = "capteur:" + String(sensorValue);
        
        // Envoyer à tous les clients connectés
        webSocket.broadcastTXT(message);
        
        Serial.print("Données envoyées: ");
        Serial.println(message);
        
        lastSensorSend = millis();
    }
    
    // Vérifier la connexion WiFi toutes les 10 secondes
    static unsigned long lastWiFiCheck = 0;
    if (millis() - lastWiFiCheck > 10000) {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("⚠️ WiFi déconnecté!");
        }
        lastWiFiCheck = millis();
    }
}