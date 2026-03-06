#include "BluetoothSerial.h"

#define SOL 15
#define LBUT 23
#define RBUT 22

#define LDIR1 18
#define LDIR2 19
#define LSPEED 0
#define LSPEED_PIN 21

#define RDIR1 17
#define RDIR2 16
#define RSPEED 1
#define RSPEED_PIN 4

#define STBY 17

#define PWM_FREQ 5000
#define PWM_RES 8

#define STOP (1 << 0)
#define DRIVE_LEFT (1 << 1)
#define DRIVE_RIGHT (1 << 2)
#define DRIVE_ANY (DRIVE_LEFT | DRIVE_RIGHT)
#define PUSH (1 << 3)
#define UNPUSH (1 << 4)

BluetoothSerial ESP_BT;

void setup()
{
  pinSetup();
  ESP_BT.begin("ROBOTECA_ESP32");
}

void pinSetup()
{
  int out[] = { LDIR1, LDIR2, RDIR1, RDIR2, STBY, SOL };
  for (int i = 0; i < 6; i++)
    pinMode(out[i], OUTPUT);

  digitalWrite(STBY, HIGH);
  
  ledcSetup(LSPEED, PWM_FREQ, PWM_RES);
  ledcAttachPin(LSPEED_PIN, LSPEED);
  
  ledcSetup(RSPEED, PWM_FREQ, PWM_RES);
  ledcAttachPin(RSPEED_PIN, RSPEED);
}

void drive(int value)
{
  if (value >= 0)
  {
    digitalWrite(LDIR1, true);
    digitalWrite(LDIR2, false);
  
    digitalWrite(RDIR1, true);
    digitalWrite(RDIR2, false);
  }
  else
  {
    digitalWrite(LDIR1, false);
    digitalWrite(LDIR2, true);

    digitalWrite(RDIR1, false);
    digitalWrite(RDIR2, true);
  }

  ledcWrite(LSPEED, abs(value));
  ledcWrite(RSPEED, abs(value));
}

void _push()
{
  digitalWrite(SOL, true);
}

void _unpush()
{
  digitalWrite(SOL, false);
}

void loop()
{
  if (ESP_BT.available())
  {
    byte action = ESP_BT.read();

    if (action & STOP)
      drive(0);
    else if (action & DRIVE_ANY)
    {
      while (!ESP_BT.available());
      byte speed = ESP_BT.read();
      if (action & DRIVE_LEFT)
        drive(speed);
      else if (action & DRIVE_RIGHT)
        drive(-speed);
    }

    if (action & UNPUSH)
      _unpush();
    else if(action & PUSH)
      _push();
  }
}
