#include "trajectory.h"
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

int num_lignes=TRAJECTORY_SIZE; // taille du tableau dans trakectory.h
int dest_lignes=800; // nombre de positions pour le robot

float theta1_G ; int micros1_G;
float theta2_G ; int micros2_G;
float theta3_G ; int micros3_G;
float roll_G ;   int microsR_G;
float theta1_D ; int micros1_D;
float theta2_D ; int micros2_D;
float theta3_D ; int micros3_D;
float roll_D ;   int microsR_D;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🚀 Démarrage ESP32...");
  
  // I2C
  Wire.begin(21, 22);  // SDA=21, SCL=22 ouverture de la communication I2C
  Wire.setClock(100000);
  pwm.begin();
  pwm.setPWMFreq(60);

  delay(500);
  
  // mise en position droite
  pwm.writeMicroseconds(0, 1500 + 96);
  pwm.writeMicroseconds(1, 1500 + 92);
  pwm.writeMicroseconds(2, 1500 + 67);
  pwm.writeMicroseconds(3, 1500 - 6);

  pwm.writeMicroseconds(4, 1500 + 155);
  pwm.writeMicroseconds(5, 1500 + 125);
  pwm.writeMicroseconds(6, 1500 + 194);
  pwm.writeMicroseconds(7, 1500 + 160);

  delay(10000);

  for (int k = 0; k < 4; k++) {
    int k0_G = table_depart[0][k];
    int k1_G = table_depart[1][k];
    int k2_G = table_depart[2][k];
    int k3_G = table_depart[3][k];

    int k0_D = table_depart[4][k];
    int k1_D = table_depart[5][k];
    int k2_D = table_depart[6][k];
    int k3_D = table_depart[7][k];
    
  pwm.writeMicroseconds(0, k0_G + 96);
  pwm.writeMicroseconds(1, k1_G + 92);
  pwm.writeMicroseconds(2, k2_G + 67);
  pwm.writeMicroseconds(3, k3_G - 6);

  pwm.writeMicroseconds(4, k0_D + 155);
  pwm.writeMicroseconds(5, k1_D + 125);
  pwm.writeMicroseconds(6, k2_D + 194);
  pwm.writeMicroseconds(7, k3_D + 160);
  delay(2000);
    }
  

   //    { -69.047,   44.657,   24.390,   -0.167,   22.110,   44.657,  -66.767,   -0.167},  // t=0.0000


  delay(30000);
  //Serial.println("Debut du mouvement"); 
  // debut de boucle
}


void loop() {
  // put your main code here, to run repeatedly:
for (int i = 0; i < dest_lignes; i= i+2) {
  
  int t0 = millis();

  
//  int j = i /  ;
//Serial.print("j  "); Serial.println(j);
  theta1_G = trajectory[i][0]; micros1_G = constrain(map(theta1_G, 135, -135, 500, 2500), 500, 2500);
  theta2_G = trajectory[i][1]; micros2_G = constrain(map(theta2_G, -135, 135, 500, 2500), 500, 2500);
  theta3_G = trajectory[i][2]; micros3_G = constrain(map(theta3_G, 135, -135, 500, 2500), 500, 2500);
  roll_G = trajectory[i][3];   microsR_G = constrain(map(roll_G, -135, 135, 500, 2500), 500, 2500);
  theta1_D = trajectory[i][4]; micros1_D = constrain(map(theta1_D, 135, -135, 500, 2500), 500, 2500);
  theta2_D = trajectory[i][5]; micros2_D = constrain(map(theta2_D, -135, 135, 500, 2500), 500, 2500);
  theta3_D = trajectory[i][6]; micros3_D = constrain(map(theta3_D, 135, -135, 500, 2500), 500, 2500);
  roll_D = trajectory[i][7];   microsR_D = constrain(map(roll_D, -135, 135, 500, 2500), 500, 2500);

  pwm.writeMicroseconds(0, micros1_G + 96);
  pwm.writeMicroseconds(1, micros2_G + 92);
  pwm.writeMicroseconds(2, micros3_G + 67);
  pwm.writeMicroseconds(3, microsR_G - 6);

  pwm.writeMicroseconds(4, micros1_D + 155);
  pwm.writeMicroseconds(5, micros2_D + 125);
  pwm.writeMicroseconds(6, micros3_D + 194);
  pwm.writeMicroseconds(7, microsR_D + 160);

  delay(5000);
  debug();
  
  int t1 = millis();
  
  //Serial.print("Freq loop  "); Serial.println( 1000 / (t1 - t0));
  }
}


void debug() {
  Serial.printf("theta1_G %.2f theta2_G %.2f theta3_G %.2f roll_G %.2f \n", theta1_G, theta2_G,theta3_G, roll_G );
  Serial.printf("theta1_D %.2f theta2_D %.2f theta3_D %.2f roll_D %.2f \n", theta1_D, theta2_D,theta3_D, roll_D);

  Serial.printf("ms1_G %.2f ms2_G %.2f ms3_G %.2f ms4_G %.2f \n", micros1_G, micros2_G,micros3_G, microsR_G );
  Serial.printf("ms1_D %.2f ms2_D %.2f ms3_D %.2f ms_D %.2f \n \n", micros1_D, micros2_D,micros3_D, microsR_D);

}
