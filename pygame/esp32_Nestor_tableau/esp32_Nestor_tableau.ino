#include "trajectory.h"
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

int num_lignes=800; // taille du tableau dans trakectory.h
int dest_lignes=800; // nombre de positions pour le robot

float theta1_G ; int micros1_G;
float theta2_G ; int micros2_G;
float theta3_G ; int micros3_G;
float roll_G ; int microsR_G;
float theta1_D ; int micros1_D;
float theta2_D ; int micros2_D;
float theta3_D ; int micros3_D;
float roll_D ; int microsR_D;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🚀 Démarrage ESP32...");
  
  // I2C
  Wire.begin(21, 22);  // SDA=21, SCL=22 (pins par défaut ESP32)
  Wire.setClock(100000);
  pwm.begin();
  pwm.setPWMFreq(60);
}


void loop() {
  // put your main code here, to run repeatedly:
for (int i = 0; i < dest_lignes; i++) {
  int j = i * num_lignes / dest_lignes;

  theta1_G = trajectory[i][0]; micros1_G = constrain(map(theta1_G, 135, -135, 500, 2500), 500, 2500);
  theta2_G = trajectory[i][1]; micros2_G = constrain(map(theta2_G, 135, -135, 500, 2500), 500, 2500);
  theta3_G = trajectory[i][2]; micros3_G = constrain(map(theta3_G, 135, -135, 500, 2500), 500, 2500);
  roll_G = trajectory[i][3]; microsR_G = constrain(map(roll_G, 135, -135, 500, 2500), 500, 2500);
  theta1_D = trajectory[i][4]; micros1_D = constrain(map(theta1_D, 135, -135, 500, 2500), 500, 2500);
  theta2_D = trajectory[i][5]; micros2_D = constrain(map(theta2_D, 135, -135, 500, 2500), 500, 2500);
  theta3_D = trajectory[i][6]; micros3_D = constrain(map(theta3_D, 135, -135, 500, 2500), 500, 2500);
  roll_D = trajectory[i][7];   microsR_D = constrain(map(roll_D, 135, -135, 500, 2500), 500, 2500);

  pwm.writeMicroseconds(0, micros1_G + 96);
  pwm.writeMicroseconds(1, micros2_G + 92);
  pwm.writeMicroseconds(2, micros3_G + 67);
  pwm.writeMicroseconds(3, microsR_G - 6);

  pwm.writeMicroseconds(4, micros1_D + 155);
  pwm.writeMicroseconds(5, micros2_D + 125);
  pwm.writeMicroseconds(6, micros3_D + 194);
  pwm.writeMicroseconds(7, microsR_D + 160);

  delay(20);
  debug();
  }
}


void debug() {
  Serial.printf("theta1_G %.2f theta2_G %.2f theta3_G %.2f roll_G %.2f \n", theta1_G, theta2_G,theta3_G, roll_G );
  Serial.printf("theta1_D %.2f theta2_D %.2f theta3_D %.2f roll_D %.2f \n", theta1_D, theta2_D,theta3_D, roll_D);
  Serial.printf("%d \n\n",j);
}