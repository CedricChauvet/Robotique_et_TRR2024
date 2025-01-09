// CODE BALISE Eurobot
#include<VirtualWire.h>
const byte PinTrig=10;    // bleu
//const byte PinEcho=11;    // violet
const unsigned long MEASURE_TIMEOUT=7000;   // microsec, durée min pour que écho A/R de 2,1 m
const float vitson=340.0/1000;              // vitesse en mm/s

void setup() {
Serial.begin(115200);
pinMode(PinTrig, OUTPUT);
digitalWrite(PinTrig,LOW);      //pin Trig doit être à LOW au repos
//pinMode(PinEcho,INPUT);
vw_setup(5000);                 // vitesse envoi des octets
vw_rx_start();                  // RX prêt à recevoir les messages
Serial.println(" GO ");         // pas nécessaire
}

void loop() {
  Serial.print("debut loop :");
  Serial.println(micros());
//long measure=pulseIn(PinEcho,HIGH,MEASURE_TIMEOUT);     // mesure temps écho
//float distance=measure/2.0*vitson;
//delay(5000);
byte message[VW_MAX_MESSAGE_LEN];
byte taille_message=VW_MAX_MESSAGE_LEN;
vw_wait_rx();                       // attente réception
if(vw_get_message(message,&taille_message))
{
  Serial.print("arrivée du top");
  Serial.println(micros());
  digitalWrite(PinTrig,HIGH);         // envoie pulse HIGH de 10microsec sur PinTrig
  
  delayMicroseconds(10);
  
  digitalWrite(PinTrig,LOW);          // remet la pin au repos
  Serial.print("fin d'emission");
  Serial.println(micros());
  Serial.print((char*)message);     // affiche message
}
}
