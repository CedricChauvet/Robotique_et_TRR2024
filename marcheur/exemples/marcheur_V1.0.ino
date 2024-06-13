//Libraries
#include <Wire.h>//https://www.arduino.cc/en/reference/wire
#include <Adafruit_PWMServoDriver.h>//https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library
//Constants
#define nbPCAServo 6


Adafruit_PWMServoDriver pca= Adafruit_PWMServoDriver(0x40);

// postion debout
int Zero [nbPCAServo] = {1500, 1500, 1500, 1500, 1500, 1500};
// position de depart
int Trente [nbPCAServo] = {1200, 1800, 1200, 1800, 1500, 1500};
int mouvement[nbPCAServo][4] = {{-300, 300, -300, 300}, 
                                {-300, 300, -300, -300},
                                {-300, 300, -500, -300},
                                {-300, 300, -300, 300}}; 

int state[4];

void setup(){
  //Init Serial USB
  Serial.begin(9600);
  Serial.println(F("Initialize System"));
  pca.begin();
  pca.setPWMFreq(60);   // Analog servos run at ~60 Hz updates
}
void loop(){
     
  etapes( mouvement[0], mouvement[1], 10);
  etapes( mouvement[1], mouvement[2], 10);
  etapes( mouvement[2], mouvement[3], 10);
  Serial.println("une boucle!");
  delay(2000);
}

void etapes(int i[4], int j[4],int steps){
  for(int x = 0; x<steps; x++){
    for(int k = 0; k<4;k++){      
      int commande = Zero[k] + i[k] + (j[k] - i[k]) / steps * x;
      Serial.print(commande);  
      Serial.print(", ");
      pca.writeMicroseconds(k,commande]);
      delay(20); // delai de securité!!!
      }
    Serial.println(" ");
    delay(500);
  }
}
