#include "trajectory.h"
int num_lignes=800; // taille du tableau dans trakectory.h
int dest_lignes=800; // nombre de positions pour le robot
void setup() {
  // put your setup code here, to run once:
Serial.begin(115200);
}


void loop() {
  // put your main code here, to run repeatedly:
for (int i = 0; i < dest_lignes; i++) {
  int j = i * num_lignes / dest_lignes;
  float theta1_G = trajectory[i][0]; theta1_G = constrain(map(theta1_G, 135, -135, 500, 2500), 500, 2500);
  float theta2_G = trajectory[i][1]; theta2_G = constrain(map(theta2_G, 135, -135, 500, 2500), 500, 2500);
  float theta3_G = trajectory[i][2]; theta3_G = constrain(map(theta3_G, 135, -135, 500, 2500), 500, 2500);
  float roll_G = trajectory[i][3]; roll_G = constrain(map(roll_G, 135, -135, 500, 2500), 500, 2500);
  float theta1_D = trajectory[i][4]; theta1_D = constrain(map(theta1_D, 135, -135, 500, 2500), 500, 2500);
  float theta2_D = trajectory[i][5]; theta2_D = constrain(map(theta2_D, 135, -135, 500, 2500), 500, 2500);
  float theta3_D = trajectory[i][6]; theta3_D = constrain(map(theta3_D, 135, -135, 500, 2500), 500, 2500);
  float roll_D = trajectory[i][7];   roll_D = constrain(map(roll_D, 135, -135, 500, 2500), 500, 2500);
  Serial.printf("theta1_G %.2f theta2_G %.2f theta3_G %.2f roll_G %.2f \n", theta1_G, theta2_G,theta3_G, roll_G );
  Serial.printf("theta1_D %.2f theta2_D %.2f theta3_D %.2f roll_D %.2f \n", theta1_D, theta2_D,theta3_D, roll_D);
  Serial.printf("%d \n\n",j);

  pwm.writeMicroseconds(0, theta1_G + 96);
  pwm.writeMicroseconds(1, theta2_G + 92);
  pwm.writeMicroseconds(2, theta3_G + 67);
  pwm.writeMicroseconds(3, roll_G - 6);

  pwm.writeMicroseconds(4, theta1_D + 155);
  pwm.writeMicroseconds(5, theta2_D + 125);
  pwm.writeMicroseconds(6, theta3_D + 194);
  pwm.writeMicroseconds(7, roll_D + 160);

  delay(20);
  }
}
