#include <Servo.h>

Servo servo2;  
Servo servo1;
const int s1 = 6;
const int s2 = 5;
const int signal = 7;

int pos = 0;

void setup() {
  servo1.attach(s1); 
  servo2.attach(s2);
  pinMode(signal, INPUT);  
}

void loop() {
   if (digitalRead(signal)){
    servo1.write(90);
    servo2.write(0);
   } 
   else{
    servo1.write(0);
    servo2.write(90);
   }               
}