#include <SPI.h>
#include <SD.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;  // constructeur pour le gyroscope

const int chipSelect = SDCARD_SS_PIN;
File dataFile;

long int t0; // T0 est le chronometre, il est déclenché entre le setup et le loop
float x=0;
float Y1;
float Y2;
float Y3;
float t;


int RPWMG=3;                    // pin D5 reçoit PWM pour marche AV mot G
int LPWMG=2;                    // pin D6 reçoit PWM pour marche AR mot G
int RPWMD=0;                    //          id pour mot D
int LPWMD=1;                   //              id
int motG = 5;                   // pin 2 reçoit les pulses de encodeur/moteur G
int motD = 6;                   // pin 3 reçoit les pulses de encodeur/moteur D




//String title[18] = ["temps","freqLoop","valeurAvant","valeurArriere","alpha","distance","erreur1","erreur2","erreur3","erreur","K1","K2","K3","pwmGauche","pwmDroit","VITG","VITD","gyro"];


String colonnes = "temps , freqLoop , valeurAvant , valeurArriere , alpha , distance , erreur1 , erreur2 , erreur3 , erreur , K1 , K2 , K3 , pwmGauche , pwmDroit , VITG , VITD , gyro";
long valeurAvant;
long valeurArriere;

String monFichier = "TEST.CSV";


float VITD;
float VITG;
float deltaT_D[2];
float deltaT_G[2];
float deltaT_Loop[2];
float freqLoop;

//long pulscountG=0;          // nb de pulses comptés par encodeur moteur G
//long pulscountD=0;          // nb de pulses comptés par encodeur moteur D

//float distParcourueG=0;
//int troncons[]={7000,27730};
//int tourActuel=5;

float nb_tour_sec_encodG;
float nb_tour_sec_encodD;


int pwmDroit;
int pwmGauche;
float gyro;

int l;
float alpha;
float erreur1;  // erreur relative à alpha
float erreur2;  // erreur relative a la distance mur
float erreur3;  // erreur relative au gyroscope
float erreur;   // somme des erreurs

float K=1.;                           // coefficient de proportionnnalité vitesses roues G et D
float deltaV;
float corr=0.0;

float consigneD=250.0;                // consigne de suivi de la bordure à la distance D = .... mm
float consigneAlpha=0.0;               // consigne de suivi de la bordure avec un angle Alpha = 0 
float K1;
float K2;
float K3;
float Ke;       // Ke est le multiplicatif d'erreur

void compteurG() {
  deltaT_G[1] = deltaT_G[0];
  deltaT_G[0] = micros();
//  pulscountG++; 
//Serial.print(" okay  ");
//nb_tour_sec_encodG=(1000000.0)/(17*t);                 // nombre tours/s roue encodeur sur 1000 000 microsec (1 tour=17 pulses)
//VITroueG= nb_tour_sec_encodG*60./6;             //  vitesse t/mn de rotation de l'axe de sortie moteur après démultiplication de 6
//VITG= VITroueG*60*3.1416*(8.6/100000.0);            // vitesse km/h équivalent du véhicule avec roue diamètre 8,6 cm
}

void   compteurD() {
  deltaT_D[1] = deltaT_D[0];
  deltaT_D[0] = micros();
//  pulscountD++;
//distParcourueG += 15.71;
//nb_tour_sec_encodD=(1000000.0)/(17*t);                 // nombre tours/s roue encodeur sur 1000 000 microsec (1 tour=17 pulses)
//VITroueD= nb_tour_sec_encodD*60./6;            //  vitesse t/mn de rotation de l'axe de sortie moteur après démultiplication de 6
//VITD= VITroueD*60*3.1416*(8.6/100000.0);            // vitesse km/h équivalent du véhicule avec roue diamètre 8,6 cm
}



void setup() {
  
  Wire.begin();
  
  pinMode(RPWMG,OUTPUT);
  pinMode(LPWMG,OUTPUT);
  pinMode(RPWMD,OUTPUT);
  pinMode(LPWMD,OUTPUT);
  pinMode(7,INPUT_PULLUP);
  pinMode(5,INPUT_PULLUP);


  // interruptions d'odommetrie roues gauche et drite
  attachInterrupt(digitalPinToInterrupt(5),compteurG,RISING);
  attachInterrupt(digitalPinToInterrupt(7),compteurD,RISING);


//  Serial.begin(9600);
//    while (!Serial) {
//    ; // wait for serial port to connect. Needed for native USB port only
//  }
  
  // initialise la carte SD
  // Serial.print("Initializing SD card...");

  // see if the card is present and can be initialized:
  if (!SD.begin(chipSelect)) {
  //   Serial.println("Card failed, or not present");
    // don't do anything more:
    while (1);
  }
  delay(1000);
   //  Serial.println("card initialized.");
    // open the file. note that only one file can be open at a time,
  // so you have to close this one before opening another.
  SD.remove(monFichier);
  delay(1000);
  dataFile = SD.open(monFichier, FILE_WRITE);
  //Serial.println("File opened.");
  dataFile.print(colonnes);
  dataFile.write("\n");
  
  dataFile.close();

// Initialise le gyrodscope
  //Serial.println("Adafruit MPU6050 test!");

  // Try to initialize!
  if (!mpu.begin()) {
    //Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  //Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
  // Serial.print("Accelerometer range set to: 2 G     ");
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  // Serial.print("Gyro range set to: +/- 250/sec     ");
  mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);
  //Serial.println("Filter bandwidth set to: 44 Hz");
  

  delay(5000);
  t0=millis(); // lance le chronometre de course
}
 

void loop() {
  //  analogWrite(RPWMG,80);  
 // analogWrite(RPWMD,80);  
     // fréquence du loop()
     deltaT_Loop[1]=deltaT_Loop[0];  
     deltaT_Loop[0]=millis();
     freqLoop =  1000.0/(deltaT_Loop[0]-deltaT_Loop[1]);
     //Serial.println(freqLoop);
  if(millis() -t0 <10000){       // le temps d'un essai est fixé à 5 secondes
     mesureVit();
     mesureGyro();
     mesureLidar();
     action();
     //debug();
     //
     
     ecritSD();
  }
  else{
    analogWrite(RPWMG,0);  
    analogWrite(RPWMD,0);
    dataFile = SD.open(monFichier, FILE_WRITE);
    dataFile.close();
    delay(10000000);
  }
  
} 
void action(){
  Ke = 1;
  if(erreur > 0){
    pwmGauche = 80;
    pwmDroit = Ke * erreur + 80.0;
  }
  if(erreur < 0){
    pwmGauche = -1.0 * Ke * erreur + 80.0;
    pwmDroit = 80;
  }
  analogWrite(RPWMG,pwmGauche);  
  analogWrite(RPWMD,pwmDroit);  
}

void ecritSD(){
  String dataString = String((millis()-t0)/1000.0);
  dataString +=(",") ;
  dataString += String(freqLoop);
  dataString +=(",") ;
  dataString += String(valeurAvant);
  dataString +=(",") ;
  dataString += String(valeurArriere);
  dataString +=(",") ;
  dataString += String(alpha);
  dataString +=(",") ;
  dataString += String(valeurAvant-40);
  dataString +=(",") ;
  dataString += String(erreur1);
  dataString +=(",") ;
  dataString += String(erreur2);
  dataString +=(",") ;
  dataString += String(erreur3);
  dataString +=(",") ;
  dataString += String(erreur);
  dataString +=(",") ;
  dataString += String(K1);
  dataString +=(",") ;
  dataString += String(K2);
  dataString +=(",") ;
  dataString += String(K3);
  dataString +=(",") ;
  dataString += String(pwmGauche);
  dataString +=(",") ;
  dataString += String(pwmDroit);
  dataString +=(",") ;  
  dataString += String(VITG);
  dataString +=(",") ;
  dataString += String(VITD);
  dataString +=(",") ;
  dataString += String(gyro);
  



  // if the file is available, write to it:
  dataFile = SD.open(monFichier, FILE_WRITE);
  if (dataFile) {
    dataFile.println(dataString);
    dataFile.close();
    // print to the serial port too:
    //Serial.println(dataString);
  }
  // if the file isn't open, pop up an error:
  else {
    //Serial.println("error opening datalog.txt");
  }

}
  
void mesureGyro(){

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  gyro = g.gyro.z * 360.0 / 6.2832;
//  Serial.print("Rotation X: ");
//  Serial.print(g.gyro.x);
//  Serial.print(", Y: ");
//  Serial.print(g.gyro.y);
//  Serial.print(", Z: ");
//  Serial.print(gyro);
//  Serial.println(" deg/s");


}


void mesureVit(){
  VITD = (3.1416*0.086 * 10000.0)/(deltaT_D[0]-deltaT_D[1]);
  if(micros()-deltaT_D[0]>500000) VITD=0.0;
  VITG = (3.1416*0.086)/(deltaT_G[0]-deltaT_G[1])*10000.0;
  if(micros()-deltaT_G[0]>500000) VITG=0.0;
}
void mesureLidar(){
      Wire.beginTransmission(0x71);
      Wire.write('D'); 
      Wire.endTransmission();
      Wire.requestFrom(0x71,2);
      valeurAvant = Wire.read();
      // receive MSB byte
      valeurAvant = valeurAvant<<8 | Wire.read(); // receive LSB byte and put them together
      //Serial.print(valeurAvant);
      //Serial.print("  ");
      
      Wire.beginTransmission(0x10);
      Wire.write('D'); 
      Wire.endTransmission();
      Wire.requestFrom(0x10, 2);
      valeurArriere = Wire.read();
      // receive MSB byte
      valeurArriere = valeurArriere<<8 | Wire.read(); // receive LSB byte and put them together
      //Serial.println(valeurArriere);
      delay(50); 
      // delay as required (13ms or higher in default single step mode)
      
      alpha = atan2(int((valeurAvant-40)-valeurArriere),220)*180.0/3.14159;
      K1 = 1.5;
      K2 = 0.5;
      K3= -1;
      erreur1 = K1 *(consigneAlpha-alpha);
      erreur2 = K2 * (consigneD-(valeurAvant-40.0)); 
      erreur3 = K3 * gyro;
      erreur = erreur1 + erreur2;
 }

 void debug(){
  Serial.print("Val Avant ");
  Serial.print(valeurAvant);
  Serial.print(" Val Arriere ");
  Serial.print(valeurArriere);
  Serial.print(" alpha ");
  Serial.println(alpha);
  //    Serial.print("pulsecountG");
  //   Serial.print(pulscountD);
  //   Serial.print(" deltaT  ");
  //   Serial.println(VITD);

  
 }
