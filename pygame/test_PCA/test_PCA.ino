#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

void setup() {

  Serial.begin(115200);
  delay(1000);
  Serial.println("Démarrage...");
  
    // I2C et PWM
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(60);
  Serial.println("PWM initialisé");
}

void loop() {
  // put your main code here, to run repeatedly:
  pwm.writeMicroseconds(1, 1000);
  delay(1000);
}
