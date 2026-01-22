#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

uint16_t currentPWM = 307;  // Valeur de départ

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Wire.begin();
  Wire.setClock(100000);
  
  pwm.begin();
  pwm.setPWMFreq(50);
  delay(100);
  
  pwm.setPWM(8, 0, currentPWM);
  
  Serial.println("=== Calibration RDS3225 ===");
  Serial.println("Commandes:");
  Serial.println("  + ou w : +1 PWM");
  Serial.println("  - ou s : -1 PWM");
  Serial.println("  ] ou d : +10 PWM");
  Serial.println("  [ ou a : -10 PWM");
  Serial.println("  p : afficher PWM actuel");
  Serial.println("  m : position MIN (205)");
  Serial.println("  c : position MID (307)");
  Serial.println("  x : position MAX (410)");
  Serial.println("");
  printPWM();
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    
    switch(cmd) {
      case '+':
      case 'w':
        currentPWM++;
        updateServo();
        break;
        
      case '-':
      case 's':
        currentPWM--;
        updateServo();
        break;
        
      case ']':
      case 'd':
        currentPWM += 10;
        updateServo();
        break;
        
      case '[':
      case 'a':
        currentPWM -= 10;
        updateServo();
        break;
        
      case 'p':
        printPWM();
        break;
        
      case 'm':
        currentPWM = 205;
        updateServo();
        Serial.println("→ MIN");
        break;
        
      case 'c':
        currentPWM = 307;
        updateServo();
        Serial.println("→ MID théorique");
        break;
        
      case 'x':
        currentPWM = 410;
        updateServo();
        Serial.println("→ MAX");
        break;
    }
  }
}

void updateServo() {
  // Limites de sécurité
  if (currentPWM < 150) currentPWM = 150;
  if (currentPWM > 500) currentPWM = 500;
  
  pwm.setPWM(8, 0, currentPWM);
  printPWM();
}

void printPWM() {
  Serial.print("PWM: ");
  Serial.print(currentPWM);
  Serial.print("\t≈ ");
  Serial.print((currentPWM * 20000) / 4096);
  Serial.println(" µs");
}