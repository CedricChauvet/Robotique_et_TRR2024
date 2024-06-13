//Libraries
#include <Wire.h>//https://www.arduino.cc/en/reference/wire
#include <Adafruit_PWMServoDriver.h>//https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library
//Constants
#define nbPCAServo 6



int Zero [nbPCAServo] = {1500,1500,1500,1500,1500};
int MIN_IMP [nbPCAServo] ={500, 500, 500, 500, 500, 500};
int MAX_IMP [nbPCAServo] ={2500, 2500, 2500, 2500, 2500, 2500};
int MIN_ANG [nbPCAServo] ={0, 0, 0, 0, 0, 0};
int MAX_ANG [nbPCAServo] ={180, 180, 180, 180, 180, 180};
//Objects
Adafruit_PWMServoDriver pca= Adafruit_PWMServoDriver(0x40);
void setup(){
//Init Serial USB
Serial.begin(9600);
Serial.println(F("Initialize System"));
pca.begin();
pca.setPWMFreq(60);   // Analog servos run at ~60 Hz updates
}
void loop(){
  for(int i = 0; i<nbPCAServo;i++){
  pca.writeMicroseconds(i,Zero[i]);delay(10);  
}
