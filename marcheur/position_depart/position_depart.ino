#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <math.h>
// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Depending on your servo make, the pulse width min and max may vary
// il faudrait encore modifier ces deux variable de maniere plus limitante  pour le
// mouvement mais qui protè
#define SERVOMIN  125 // this is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  575 // this is the 'maximum' pulse length count (out of 4096)

// points milieux de chaques  servomoteurs
int p1 = 94;
int p2 = 93;
int p3 = 90;
int p4 = 95;

// dimensions du  robot
float h  = 18.5; // hauteur du robot
float l = 11.0; // longeur tibia considerant que les deux parties de la jambe aient meme longueur

const float pi = 3.14159267;

void setup() {
  Serial.begin(9600);
  Serial.println("16 channel Servo test!");

  pwm.begin();
  Serial.println("angletopulse depart:");
  Serial.println(angleToPulse(p3+43.5));
    Serial.println("angletopulseArrivée:");
  Serial.println(angleToPulse(p3 +12.5));
 
 
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates

   pwm.setPWM(1, 0, angleToPulse(p1-30)) ;      
   pwm.setPWM(2, 0, angleToPulse(p2+30)) ;      
   pwm.setPWM(3, 0, angleToPulse(p3+30)) ;      
   pwm.setPWM(4, 0, angleToPulse(p4-30)); 
   pwm.setPWM(8, 0, angleToPulse(90-20)); 
   pwm.setPWM(9, 0, angleToPulse(90+20)); 
}

// calculée par l'exercice 3 de la documentation
// elle demontre que 2 jambes assymetriques, peuvent etre pilotées 
// tout en gardant une hauteur constante, voir calcul...

void loop() {
for (int i = 0; i<40;i++){
 pwm.setPWM(8, 0, angleToPulse(90)); 

 pwm.setPWM(9, 0, angleToPulse(90-i));
 delay(50);
  }

delay(5000);

}

int angleToPulse(int angle){
   
   // mapping de 0 a 180
   //int pulse = map(ang,0, 180, SERVOMIN,SERVOMAX);
   
   // mapping de 20 a 160 degres, avec constrain pour protection des moteurs
   angle = constrain(angle, 20, 160);
   int pulse = map(angle,20, 160, 175,525);
   
//   Serial.print("atp_Angle: ");Serial.print(angle);
//   Serial.print("atp_pulse: ");Serial.println(pulse);
   return pulse;
}

int pulseToAngle(int pulse){
   
   // mapping de 0 a 180
   //int pulse = map(ang,0, 180, SERVOMIN,SERVOMAX);
   
   // mapping de 20 a 160 degres, avec constrain pour protection des moteurs
   pulse = constrain(pulse, 175, 525);
   int angle = map(pulse, 175, 525, 20, 160);
//   
//   Serial.print("pta_Angle: ");Serial.print(angle);
//   Serial.print("pta_pulse: ");Serial.println(pulse);
   return angle;
}

//
//float degrees(float radians) {
//  return radians / 2 / pi * 360;
//}
//float radians(float degrees) {
//  return degrees / 360 * 2 * pi;
//}
/*
   // jambe gauche avancé
   pwm.setPWM(1, 0, angleToPulse(p1-12.5));
C   pwm.setPWM(3, 0, angleToPulse(p3+43.5));
   pwm.setPWM(4, 0, angleToPulse(p4-30)); 
  *
  *
  *
   // jambe gauche reculée
   pwm.setPWM(1, 0, angleToPulse(p1-43));
   pwm.setPWM(2, 0, angleToPulse(p2+30)) ;      
   pwm.setPWM(3, 0, angleToPulse(p3+12.5));
   pwm.setPWM(4, 0, angleToPulse(p4-30)); 
   
 */
