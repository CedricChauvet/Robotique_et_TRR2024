/* Programme HERMES complet issu du code "Hermes basique Uart odo" (incomplet) testé à 17 km/h sur banc le 22 décembre 2025.
4 lasers TF mini Plus, ports série harware  pour les 2 lasers latéraux et ports virtuels pour les 2 lasers frontaux
en utilsant la librairies SofWareSerial
La lesture des lasers s'effectue par la méthode de lecture directe des ports série
La fréquence de lecture des lasers est celle par défaut : 100Hz
 */

#include "SoftwareSerial.h"

#include "ESP32Servo.h"              // librairie servo ESP32
#include "ESP32PWM.h"                // associée à la librairie ESP32Servo.h

#include "WiFi.h"
#include "PubSubClient.h"
#include  "Wire.h"
  // WiFi 
const char *ssid = "trollworld"; // Entrez votre SSID WiFi  
const char *password = "je vais jouer a la wii"; // Entrez votre mot de passe WiFi 
  
// MQTT Broker 
const char *mqtt_broker = "192.168.1.14";     // Adresse Ip du PC hébergeant Mosquitto
const char *topic = "test";                   //Topic entrant sur le broker
const char *intopic = "testout";              //Topic sortant sur le broker
String chaine = " ";                          // chaine de caractère contenant le message 
const char *mqtt_username = ""; 
const char *mqtt_password = ""; 
const int mqtt_port = 1883; 
WiFiClient espClient; 
PubSubClient client(espClient); 

Servo myservo;                       // déclaration objet servo

EspSoftwareSerial::UART myPort;      // Déclaration objet serial virtuel par librairie softWareserial
EspSoftwareSerial::UART myPortD;     // Déclaration objet serial virtuel par librairie softWareserial

                  // PINS
const int pinTpntH=12;                // pin pont en H forward
const int pinTpntHrev=18;             // pin pont en H reverse
const int pinServo=5;                 // pin servo direction  
const int pinOdo=13;                   // pin odométrie
int angleDefault=88;                  // variable de commande servo direction à braquage nul
int angleBraq=angleDefault;           // variable commande braquage

                  // Declaration des ports serial des capteurs lasers
int RXD1=16;              // RX serial UART du ESP 32  à connecter au TX du laser  AV G
int TXD1=17;              // TX serial UART du ESP 32  à connecter au RX du laser  AV G
int RXD2=14;              // RX serial UART du ESP 32  à connecter au TX du laser AV droit
int TXD2=27;              // TX serial UART du ESP 32  à connecter au RX du laser  AV droit
int RXD3=33;              // RX serial du ESP 32 sur un port non uart laser à connecter au TX du laser Frontal Gauche câble vert
int TXD3=32;              // TX serial du ESP 32 sur un port non uart laser à connecter au RX du laser Frontal Gauche câble blanc
int RXD4=26;              // RX serial du ESP 32 sur un port non uart laser à connecter au TX du laser Frontal Droite câble vert
int TXD4=25;              // TX serial du ESP 32 sur un port non uart laser à connecter au RX du laser Frontal Droite câble  blanc

                    // variables odométrie 
unsigned long t;                                        // délai entre deux lecture du pignon pour odométrie
unsigned long nbPignon=0;                               // cumul du nbre de tours roue
unsigned long deltaNbPignon;
unsigned long lastNbPignon=0;                               // cumul du nbre de tour pignon
unsigned long deltaMicro;                               
unsigned long lastMicro;                               // pour calcul délai odométrie
float cumDist;                                          // distance parcourue cumulée en cm
//float cumDistInt;                                       // distance parcourue cumulée en cm calculée sur interruption
float nb_tour_sec;                                  // nbre de tour/s roue
//unsigned long curseTime = 90000;                        // Compteur de temps total course en millis (exempl 60 secondes = 60 000
unsigned long curseTime = 10000;                        // Compteur de temps total course en millis (exempl 60 secondes = 60 000
unsigned long lastCurseTime;                            // Temps début course  
                      
                    // variables asservissement vitesse
float VIT;                                              // vitesse calculée en KM/H
float VitInt;                                           // vitesse calculée en KM/H par interrupt
int PwmVIT=0;                     // Initialisation de la valeur du PWM pont en H
int lastVIT=0;
float kp=2;
float kd=2;
float corrDebug;
int pwmMult=2.0;
int pwmconst=0;
                    // variables utilisées pour le freinage
bool okFrein=false;                               // indicateur condition necessitant freinage initialisé à false
bool neutre = false;                              // indicateur état précédent commande pont en H 
int minDist=300;                                   // distance mini capteur frontal déclenchant le freinage
int PwmReverse=180;                                 // valeur du Pwm reverse
int PwmFrein = PwmReverse;
float consiTroncon =0.0;                          // consigne vitesse donnée par la table troncon
float consi=0.0;                                  // consigne vitesse effective
float consiVite =15.0;                               // consigne vitesse ligne droite
float consiLent =9.0;                               // consigne vitesse virages
long int t0frein =0;                              // compteur millis pour intervalle coup de frein
long int dfrein=5;                                // durée action freinage en ms.
bool debFrein = false;                            // indicateur première boucle de freinageconsi=consiVite;

float tronCon[16][2] {         // tableau 16 tronçons : cm et km/h 
            {0,2},                        // 
            {50,3},                       // 
            {100,4},                      // 
            {550,0},                     // 6m: premier portique
            {1100,0},                     //  Charbonnière     
            {3031,7},                     // portique          
            {5462,4},                     // Portique  
            {5562,7},                     //
            {7893,4},                     // Portique
            {8093,7},                     //
            {10324,4},                    // Portique
            {10524,7},
            {12754,4},                    // Dernier Portique
            {13050,0},                    // fin de course
            {132000,0},                                                
            {999999,0}                    
 };
 

int lgTroncon =(sizeof(tronCon)/sizeof(tronCon[0]))-1;                    
               // Acquisitions mesures capteurs laser
int FAR;                                         //mesure du laser AV G
int FAV;                                         //mesure du laser AV droit
int dgau;        //dist cm mesurée laser AV G changement de variable
int ddroit;        //dist cm mesurée laser AV D
int FAF;                                         //mesure du laser frontal gauche
int FAFD;                                        //mesure du laser frontal droite
int check;                                      //variable de contrôle checksum tampon données laser
int i;
int uart[9];       
int uart2[9];   //variable tableau stockage tampon données laser
const int HEADER=0x59;                          //entête tampon données laser
                // variables spécifiques au pilotage lasers droite
float l=19.5;                                      // distance en cm entre les deux capteurs lasers latéraux droite
float erreur;                                     // erreur totale (erreur alpha + erreur distance)
float lastErreur;
float alpha=0.0;                                  // angle alpha si deux lasers latéraux
float consigneD=50.0;                             // consigne de suivi de la bordure à la distance D
float consigneAlpha=0.;                           // consigne de suivi de la bordure avec un angle Alpha (= 0 en ligne droite)
float lastAlpha=0.0;                              // erreur précédente pour calculer le delta alpha
float lastDist=0.0;                               // erreur précédente pour calculer le delta distance
                //Coefficient pilotage lasers latéraux
float K1 = 0.5;                                    // coefficient erreur alpha
float K2 = 0.7;                                   // coefficient erreur distance
float KD1 = 0.0;                                  // coefficient delta erreur alpha
float KD2 = 0.0;                                  // coefficient delta erreur distance
                   // compteurs de temps
long int t0;                                      // valeur micros() en début de boucle
long int t1;                                      // durée d'une boucle de tratement en micros secondes

void setup() {
Serial.begin(115200);                             //initialisation vitesse port série entre esp32 et pc

MqttSetUp();                                // initialisation wifi et MQTT

initSerial();                           // Initialisation des ports série et des objets tfminiPlus
t1=micros()-t0;                                     // initialisation de t1
                // initialisation des pins
myservo.attach(pinServo);                         // déclaration objet myservo
pinMode(pinTpntH,OUTPUT);                         // initialisation pin forward pont en H
pinMode(pinTpntHrev,OUTPUT);                      // initialisation pin reverse pont en H

pinMode(pinOdo,INPUT);                // initialisation pin signal hall
attachInterrupt(pinOdo, countInterrupt,FALLING);  // appel interruption pour mesurer le nombre de tours
movServo();                                     // mise à la position neutre du servo de direction
delay(10000);
Serial.println("fin setup");
}

void loop() {
  t0=micros();                                     // chargement durée début loop  
  litLaserAV();                                    // appel fonction lecture laser droite ou laser arrière
  litLaserAR();                                    // appel fonction lecture laser gauche ou laser avant
  litLaserAF();                                    // appel fonction lecture laser frontal
  litLaserAFD();                                    // appel fonction lecture laser frontal
Erreur();                                         // appel fonction calcul erreur de trajectoire 
movServo();                                      // appel fonction commande servo de direction
compteur();
ouEstil();
asservissement_T();
motor();
debug();                                         // appel fonction affichage infos sur console.A commenter pour exploitation en course 
messageOut();                                    // chargement du contenu de message à publier 
EmetMqtt();                                      // appel fonction de pubblish message pour le broker
  if (!client.connected()) {
    Serial.println("Déconnecté");
  }
  t1=micros()-t0;                                 // chargement durée fin de boucle
}

void Erreur(){
/*alpha=atan((FAV-FAR)/l)*180/3.14159;                  // calcul angle trajectoire véhicule
float erreurAlpha=K1*(consigneAlpha-alpha) - KD1*((consigneAlpha-lastAlpha)-(consigneAlpha-alpha));
float erreurDist = K2*(consigneD-FAV) - KD2*((consigneD-lastDist)-(consigneD-FAV));
erreur= K1*(consigneAlpha-alpha)+ K2*(consigneD-FAV);   // erreur totale : erreur alpha + erreur distance
//erreur= erreurAlpha + erreurDist;                       // erreur totale : erreur alpha + erreur distance
angleBraq = (-1.07*erreur)+89.36;          //PWM pour braquage servo, fonction de loi de calibration servo
lastDist = FAV;
lastAlpha = alpha;*/
ddroit=FAV;
dgau=FAR;
erreur= 1*(dgau-ddroit);
angleBraq=(-1.07*erreur)+89.36; 
}

void ouEstil() {
  cumDist = (nbPignon)*3.1416*7.2;        // diam roue 7.2, calcul cumul de la distance en cm 
  for (int i=0; i <= 8;i++){ 
  if(cumDist >= tronCon[i][0] and cumDist < tronCon[i+1][0]){
  consi = tronCon[i][1];
  }
  }
}

void  asservissement_T(){                       // asservissement vitesse en fonction de la consigne tronçon
if(consi==0){
PwmVIT=0.;
}
else{
  int err=consi-VIT;  
  float corr= kp*err;                 // calcul erreur totale
  PwmVIT= 1*(consi+corr)+20;          // calcul du PwmVIT pour obtenir la VIT du tronçon
  //PwmVit=60;
  }
  motor(); 
}

void countInterrupt(){                // fonction appelée par l'attach interrupt
nbPignon++;
}

void compteur(){
deltaNbPignon = nbPignon - lastNbPignon;
if(deltaNbPignon >0){
deltaMicro = micros() - lastMicro;
lastNbPignon = nbPignon;
lastMicro = micros();
nb_tour_sec= deltaNbPignon /(deltaMicro/1000000.0);
VIT = (nb_tour_sec*3600)*(3.1416*7.2/100000);
cumDist = (nbPignon)*3.1416*7.2;
}
}

void movServo(){
  angleBraq=constrain(angleBraq,70,110);
  myservo.write(angleBraq);
}

void motor(){
  PwmVIT = constrain(PwmVIT, 0,100);
  analogWrite(pinTpntH,PwmVIT);
 }

void debug(){
   /* Serial.print(" A ");
    Serial.print(FAV);                             //affichage distance mesuré par le laser avant
    Serial.print(" B ");
    Serial.print(FAR);                             //affichage distance mesuré par le laser arrière
    Serial.print(" C ");
    Serial.print(FAF);                             //affichage distance mesuré par le laser frontal gauche
    Serial.print(" D ");
    Serial.print(FAFD);                             //affichage distance mesuré par le laser frontal droite */
  Serial.print("Braquage  ");Serial.print(angleBraq);
  Serial.print("   PwmVIT  ");Serial.print(PwmVIT);
  Serial.print("   D  ");Serial.print(deltaMicro);
  Serial.print("   Tours/S  ");Serial.print(nb_tour_sec);
  Serial.print("   Nb tours  ");Serial.print(nbPignon );
  Serial.print("   Distance cm  ");Serial.print(cumDist);
  Serial.print("   VIT  ");Serial.print(VIT );
  Serial.print("   F  "); 
  Serial.println(1000000/t1);                   // fréquence d'exécution de la boucle
  
}

void messageOut(){                      // chargement du contenu de message à publier 
  
  chaine = FAV + " ";                       // Laser
  chaine = chaine + FAR + " ";              // Laser
  chaine = chaine + FAF + " ";              // Laser Frontal
  chaine = chaine + FAFD + " ";             // Laser Frontal
  chaine = chaine + angleBraq + " ";        // angle braquage
  chaine = chaine + PwmVIT + " ";           // angle PWM
  chaine = chaine + deltaMicro + " ";       // deltaMicro
  chaine = chaine + nb_tour_sec + " ";      // nb_tour_sec
  chaine = chaine + nbPignon + " ";         // nbPignon
  chaine = chaine + cumDist + " ";          // cumDist
  chaine = chaine + VIT + " ";              // vitesse
  chaine = chaine + 1000000/t1 + " ";       // fréquence
  
}

void initSerial(){      // Initialisation des ports série et des objets tfminiPlus
  Serial2.begin(115200, SERIAL_8N1, RXD1, TXD1);
  Serial1.begin(115200, SERIAL_8N1, RXD2, TXD2);        
  // initialisation port série virtuel et contrôle laser frontal gauche
myPort.begin(115200, SWSERIAL_8N1, RXD3, TXD3, false);
if (!myPort) { // Si l'objet ne s'est pas initialisé, alors sa configuration n'est pas valide
  Serial.println("Configuration des broches EspSoftwareSerial invalide, vérifiez la configuration"); 
  while (1) { // boucler tant que la configuration est invalide
    delay (100);
  }
} 
  // initialisation port série virtuel et contrôle laser frontal droite
myPortD.begin(115200, SWSERIAL_8N1, RXD4, TXD4, false);
if (!myPortD) { // Si l'objet ne s'est pas initialisé, alors sa configuration n'est pas valide
  Serial.println("Configuration des broches EspSoftwareSerial invalide, vérifiez la configuration"); 
  while (1) { // boucler tant que la configuration est invalide
    delay (100);
  }
} 
}

void litLaserAV(){
  //Serial.println("test serial1 ");
  if (Serial1.available()) {                        //contrôle si data en entrées sur port série
    //Serial.println(" Serial1 ok ");
    if(Serial1.read() == HEADER) {                      //contrôler la valeur de l'entête du paquet de données présente dans l'octet 0
      uart[0]=HEADER;                               // charger cette valeur dans l'élément 0 du tableau
      if (Serial1.read() == HEADER) {                 //contrôler la valeur de l'entête du paquet de données présente dans l'octet 1
        uart[1] = HEADER;                             // charger cette valeur dans l'élément 1 du tableau
        for (i = 2; i < 9; i++) {                     // boucle de chargement des données des octets suivants dans le tableau
          uart[i] = Serial1.read();
        }
        check = uart[0] + uart[1] + uart[2] + uart[3] + uart[4] + uart[5] + uart[6] + uart[7];
        if (uart[8] == (check&0xff)){                     //contrôle de l'intégrité des données : le dernier octet fde la somme des éléménts 0 à 7 
                                                          // du tableau doit être égale à la valeur de l'éléments 8.
          FAV = uart[2] + uart[3] * 256;                   //calcul de la distance
         }
       }  
     }
   }
}

void litLaserAR(){
  //Serial.println("test serial2 ");
  if (Serial2.available()) {                        //contrôle si data en entrées sur port série
    //Serial.println(" Serial2 ok ");
    if(Serial2.read() == HEADER) {                    //contrôler la valeur de l'entête du paquet de données présente dans l'octet 0
      uart2[0]=HEADER;                                 // charger cette valeur dans l'élément 0 du tableau
      if (Serial2.read() == HEADER) {                 //contrôler la valeur de l'entête du paquet de données présente dans l'octet 1
        uart2[1] = HEADER;                             // charger cette valeur dans l'élément 1 du tableau
        for (i = 2; i < 9; i++) {                     // boucle de chargement des données des octets suivants dans le tableau
          uart2[i] = Serial2.read();
        }
        check = uart2[0] + uart2[1] + uart2[2] + uart2[3] + uart2[4] + uart2[5] + uart2[6] + uart2[7];
        if (uart2[8] == (check&0xff)){                     //contrôle de l'intégrité des données : le dernier octet fde la somme des éléménts 0 à 7 
                                                          // du tableau doit être égale à la valeur de l'éléments 8.
          FAR = uart2[2] + uart2[3] * 256;                   //calcul de la distance
         }
       }  
     }
   }
}


void litLaserAF(){
  //Serial.println("test serial3 ");
  if (myPort.available()) {                        //contrôle si data en entrées sur port série
    //Serial.println(" Serial3 ok ");
    if(myPort.read() == HEADER) {                    //contrôler la valeur de l'entête du paquet de données présente dans l'octet 0
      uart2[0]=HEADER;                                 // charger cette valeur dans l'élément 0 du tableau
      if (myPort.read() == HEADER) {                 //contrôler la valeur de l'entête du paquet de données présente dans l'octet 1
        uart2[1] = HEADER;                             // charger cette valeur dans l'élément 1 du tableau
        for (i = 2; i < 9; i++) {                     // boucle de chargement des données des octets suivants dans le tableau
          uart2[i] = myPort.read();
        }
        check = uart2[0] + uart2[1] + uart2[2] + uart2[3] + uart2[4] + uart2[5] + uart2[6] + uart2[7];
        if (uart2[8] == (check&0xff)){                        //contrôle de l'intégrité des données : le dernier octet fde la somme des éléménts 0 à 7 
                                                              // du tableau doit être égale à la valeur de l'éléments 8.
          FAF = uart2[2] + uart2[3] * 256;                   //calcul de la distance
         }
         //mesureFreqLaser();                                 // appel fonction permettant d'estimer la fréquence d'acquisition d'un laser          
       }  
     }
   }
}

void litLaserAFD(){
  //Serial.println("test serial3 ");
  if (myPortD.available()) {                        //contrôle si data en entrées sur port série
    //Serial.println(" Serial3 ok ");
    if(myPortD.read() == HEADER) {                    //contrôler la valeur de l'entête du paquet de données présente dans l'octet 0
      uart2[0]=HEADER;                                 // charger cette valeur dans l'élément 0 du tableau
      if (myPortD.read() == HEADER) {                 //contrôler la valeur de l'entête du paquet de données présente dans l'octet 1
        uart2[1] = HEADER;                             // charger cette valeur dans l'élément 1 du tableau
        for (i = 2; i < 9; i++) {                     // boucle de chargement des données des octets suivants dans le tableau
          uart2[i] = myPortD.read();
        }
        check = uart2[0] + uart2[1] + uart2[2] + uart2[3] + uart2[4] + uart2[5] + uart2[6] + uart2[7];
        if (uart2[8] == (check&0xff)){                        //contrôle de l'intégrité des données : le dernier octet fde la somme des éléménts 0 à 7 
                                                              // du tableau doit être égale à la valeur de l'éléments 8.
          FAFD = uart2[2] + uart2[3] * 256;                   //calcul de la distance
         }
         //mesureFreqLaser();                                 // appel fonction permettant d'estimer la fréquence d'acquisition d'un laser          
       }  
     }
   }
}

void MqttSetUp(){
   // Connecting to a Wi-Fi network 
 WiFi.begin(ssid, password); 
 while (WiFi.status() != WL_CONNECTED) { 
 delay(500); 
 Serial.println("Connecting to WiFi.."); 
  } Serial.println("Connected to the Wi-Fi network"); 
  //connexion au broker MQTT  
 client.setServer(mqtt_broker, mqtt_port); 
 client.setCallback(callback); 
 while (!client.connected()) { 
 String client_id = "esp32-client-"; 
 client_id += String(WiFi.macAddress()); 
 Serial.printf("The client %s connects to the public MQTT brokern", client_id.c_str()); 
 if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) { 
  Serial.println("Public EMQX MQTT broker connected"); 
  } else { 
  Serial.print("failed with state "); 
  Serial.print(client.state()); 
  delay(2000); 
  } 
  } 
  // Publish et subscribe 
  client.publish(topic, "Hi, I'm ESP32"); 
  client.subscribe(intopic);
  
}

 // Reception du message MQTT 
void callback(char *topic, byte *payload, unsigned int length) { 
Serial.print("Message arrived in topic: "); 
Serial.println(topic); 
  Serial.print("Message:"); 
  for (int i = 0; i < length; i++) { 
Serial.print((char) payload[i]); 
  } 
  Serial.println(); 
  Serial.println("-----------------------"); 
}

// Emission message MQTT
void EmetMqtt(){
  //String chaine = "Ab bc cd";
  client.publish(topic, toCharArray(chaine)); 

}

char* toCharArray(String str) {
  return &str[0];
}
