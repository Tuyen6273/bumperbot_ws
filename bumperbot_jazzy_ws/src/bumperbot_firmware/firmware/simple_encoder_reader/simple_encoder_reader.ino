#define L298N_enA  14
#define L298N_in1  26
#define L298N_in2  27
#define right_encoder_phaseA 19
#define right_encoder_phaseB 18

unsigned int right_encoder_counter = 0;
char right_encoder_sign = 'p';
double right_wheel_measure_velocity = 0.0; // rad/s
unsigned long last_measurement = 0;

#define PULSE_PER_REVOLUTION  234 //(pulse/rev)
#define RPM_TO_RADS  2* 3.14 //(rad/s = v/s*2pi)

void setup() {
  // put your setup code here, to run once:
    pinMode(L298N_enA, OUTPUT);
    pinMode(L298N_in1, OUTPUT);
    pinMode(L298N_in2, OUTPUT);

    pinMode(right_encoder_phaseA, INPUT);
    pinMode(right_encoder_phaseB, INPUT);

    attachInterrupt(right_encoder_phaseA, rightEncoderCallback, RISING);

    digitalWrite(L298N_in1, HIGH);
    digitalWrite(L298N_in2, LOW);
    
    
    Serial.begin(115200);
    last_measurement = millis();
}

void loop() {
  // put your main code here, to run repeatedly:
  
  unsigned long now = millis();
  unsigned long elapsed_ms = now - last_measurement;
  analogWrite(L298N_enA, 255);
  if(elapsed_ms >= 100)
  {
    noInterrupts();
    unsigned int pulse = right_encoder_counter;
    right_encoder_counter = 0;
    interrupts();
    last_measurement = now;

    right_wheel_measure_velocity = double(10.0*(pulse/(100.0*PULSE_PER_REVOLUTION))*RPM_TO_RADS);

    // String read_sign_encoder = right_encoder_sign + String(right_wheel_measure_velocity); 
    // Serial.println(read_sign_encoder);
    Serial.print(right_encoder_sign);
    Serial.println(right_wheel_measure_velocity, 3);
  }

}

void rightEncoderCallback()
{
  right_encoder_counter++;
  if(digitalRead(right_encoder_phaseB) == HIGH)
  {
    right_encoder_sign = 'p';
  }
  else{
    right_encoder_sign = 'n';
  }
}