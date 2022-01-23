

#include <LiquidCrystal_I2C.h>
#include <Wire.h>
LiquidCrystal_I2C lcdekranim2(0x27,16,2);

void setup()
{
  Serial.begin(9600);
  
  pinMode(13,OUTPUT);
}

void loop()
{
  if(Serial.available()>0)
  {
    
    int a=Serial.read();
    lcdekranim2.init();
    lcdekranim2.backlight();
  
    if (a=='2') // arduinoya 2 gelirse 
    {
    digitalWrite(13,HIGH);
    delay(500);
    for (int x = 16; x >= 0; x--)
      {
      lcdekranim2.setCursor(x, 0);
      lcdekranim2.print("Yolda anomali var");
      lcdekranim2.setCursor(x, 1);
      lcdekranim2.print("Yavaslayiniz");
      delay(500);
      digitalWrite(13,LOW);
      delay(500);
      digitalWrite(13,HIGH); 
      lcdekranim2.setCursor(x, 0);
      lcdekranim2.print(" ");
      lcdekranim2.setCursor(x, 1);
      lcdekranim2.print(" ");
      lcdekranim2.clear();
     
      }
      digitalWrite(13,LOW);
      
    }
    if (a=='4') // arduinoya 4 gelirse
    {
    digitalWrite(13,HIGH);
    delay(500);
    for (int x = 16; x >= 0; x--)   
      { 
      delay(500);
      digitalWrite(13,LOW);
      delay(500);
      digitalWrite(13,HIGH); 
      
      }
      digitalWrite(13,LOW);
      }

    }
  }
  
