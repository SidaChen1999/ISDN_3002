#define LEDPIN 16
#define buttonPin 5
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(buttonPin,INPUT);
  pinMode(LEDPIN, OUTPUT);
  delay(100);
  Serial.println("Started");
}
int loop_count = 0;
void loop() {
  // put your main code here, to run repeatedly:
  if (digitalRead(buttonPin) == LOW){
    Serial.println(0);
  }
  else if (digitalRead(buttonPin) == HIGH) {
    Serial.println(1);
  }
  ledBlink();
  
}

void ledBlink(){
  if (loop_count % 2 == 0)
  {
    digitalWrite(LEDPIN, HIGH);
  }
  else
  {
    digitalWrite(LEDPIN, LOW);
  }
  loop_count++;
}
