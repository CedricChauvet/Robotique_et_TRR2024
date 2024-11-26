#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Depending on your servo make, the pulse width min and max may vary
#define SERVOMIN  125 // this is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  575 // this is the 'maximum' pulse length count (out of 4096)

void setup() {
  Serial.begin(9600);
  Serial.println("16 channel Servo test!");

  pwm.begin();
  
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
}

void loop() {
//    for( int angle =0; angle<181; angle +=10){
//      delay(50);
//        pwm.setPWM(0, 0, angleToPulse(angle));
//    }
 
  delay(2000);
  pwm.setPWM(1, 0, angleToPulse(55));
  pwm.setPWM(2, 0, angleToPulse(90));
  pwm.setPWM(3, 0, angleToPulse(125));
  pwm.setPWM(4, 0, angleToPulse(90));
  delay(2000);
}

int angleToPulse(int ang){
   int pulse = map(ang,0, 180, SERVOMIN,SERVOMAX);
   Serial.print("Angle: ");Serial.print(ang);
   Serial.print(" pulse: ");Serial.println(pulse);
   return pulse;
}
