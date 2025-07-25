#include "esp_camera.h"
#include <WiFi.h>

const char* ssid = "Bbox-BFE7AC14";
const char* password = "ITetudes.256";


// Configuration caméra AI Thinker (ESP32-CAM standard)
camera_config_t config = {
  .pin_pwdn       = 32,
  .pin_reset      = -1,
  .pin_xclk       = 0,
  .pin_sccb_sda   = 26,
  .pin_sccb_scl   = 27,
  .pin_d7         = 35,
  .pin_d6         = 34,
  .pin_d5         = 39,
  .pin_d4         = 36,
  .pin_d3         = 21,
  .pin_d2         = 19,
  .pin_d1         = 18,
  .pin_d0         = 5,
  .pin_vsync      = 25,
  .pin_href       = 23,
  .pin_pclk       = 22,
  .xclk_freq_hz   = 20000000,
  .ledc_timer     = LEDC_TIMER_0,
  .ledc_channel   = LEDC_CHANNEL_0,
  .pixel_format   = PIXFORMAT_JPEG,
  .frame_size     = FRAMESIZE_VGA,
  .jpeg_quality   = 12, 
  .fb_count       = 1
};


WiFiServer server(80);

void startCamera() {
  for (int i = 0; i < 5; i++) {
    esp_err_t err = esp_camera_init(&config);
    if (err == ESP_OK) return;
    Serial.printf("Camera init failed (attempt %d): 0x%x\n", i + 1, err);
    delay(2000);
  }
  ESP.restart();
}
void sendIndexPage(WiFiClient &client) {
  String page =
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html\r\n"
    "\r\n"
    "<!DOCTYPE html><html><head><title>ESP32-CAM Stream</title></head><body>"
    "<h1>ESP32-CAM Streaming</h1>"
    "<img src=\"/stream\" style=\"max-width: 100%; height: auto;\"/>"
    "</body></html>";
  
  client.print(page);
}



void streamVideo(WiFiClient &client) {
  // Envoi en une seule fois des headers HTTP pour indiquer que la réponse est un flux multipart MJPEG
  String headers = 
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
    "\r\n"; // Ligne vide séparant headers et contenu
  client.print(headers);
  
  // Tant que le client est connecté 
  while (client.connected()) {
    // Capture d'une image via la caméra
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Erreur : capture caméra échouée.");
      continue; // On continue la boucle pour essayer une nouvelle capture
    }

    int taille = fb->len;        // Taille en octets de l'image JPEG capturée
    uint8_t* image = fb->buf;    // Pointeur vers les données binaires de l'image

    // Envoi du délimiteur de la frame dans le flux multipart
    client.print("--frame\r\n");
    // Envoi des headers spécifiques à cette image (type MIME et taille)
    client.print("Content-Type: image/jpeg\r\n");
    client.printf("Content-Length: %u\r\n\r\n", taille);

    // Envoi des données binaires brutes de l'image JPEG
    // Ici client.write est indispensable : il envoie les octets tels quels, sans transformation
    // Ce qui garantit que l'image ne sera pas corrompue en cours de transmission
    client.write(image, taille);

    // Fin de la partie image avec un saut de ligne
    client.print("\r\n");

    // Libération du buffer image pour la prochaine capture
    esp_camera_fb_return(fb);

    delay(10); // Petite pause pour éviter de saturer la connexion
  }
}



void setup() {
  Serial.begin(115200);
  Serial.println("Booting...");

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  startCamera();
  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (!client) {
    delay(10);
    return;
  }

  // Lecture complète des headers HTTP
  String req = "";
  while (client.connected()) {
    String line = client.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) break;
    req += line + "\n";
  }

  Serial.println("Requête reçue:");
  Serial.println(req);

  if (req.indexOf("GET /stream") >= 0) {
    streamVideo(client);
  } else {
    sendIndexPage(client);
  }

  client.stop();
}