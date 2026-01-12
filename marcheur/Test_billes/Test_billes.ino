#include <Adafruit_PWMServoDriver.h>


Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();



void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println("16 channel Servo test!");

  pwm.begin();
  Serial.println("angletopulse depart:");
  Serial.println(angleToPulse(90));
    Serial.println("angletopulseArrivée:");
  Serial.println(angleToPulse(90));

  delay(5000);
 
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
}

void loop() {
  // put your main code here, to run repeatedly:
   pwm.setPWM(15, 0, angleToPulse(110));
   pwm.setPWM(14, 0, angleToPulse(90));
   delay(1000);
   pwm.setPWM(15, 0, angleToPulse(90));
   pwm.setPWM(14, 0, angleToPulse(70));
   delay(1000);



}


int angleToPulse(float angle){
   
   // mapping de 0 a 180
   //int pulse = map(ang,0, 180, SERVOMIN,SERVOMAX);
   
   // mapping de 20 a 160 degres, avec constrain pour protection des moteurs
   angle = constrain(angle, 20, 160);
   int pulse = map(angle,20, 160, 175,525);
   
//   Serial.print("atp_Angle: ");Serial.print(angle);
//   Serial.print("atp_pulse: ");Serial.println(pulse);
   return pulse;
}
