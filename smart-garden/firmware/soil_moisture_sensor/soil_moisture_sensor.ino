const int moistureSensorPin = A0;
const long interval = 5000;
unsigned long previousMillis = 0;

// Calibration values
int airValue = 669;  // Value in air (completely dry) - adjust this!
int waterValue = 202;   // Value in water (completely wet) - adjust this!

void setup() {
  Serial.begin(9600);
  pinMode(moistureSensorPin, INPUT);
}

void loop() {
  unsigned long currentMillis = millis();
  
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Read the analog value
    int sensorValue = analogRead(moistureSensorPin);
    
    // Map to moisture percentage with the calibrated values
    int moisturePercentage = map(sensorValue, airValue, waterValue, 0, 100);
    
    // Constrain to prevent values outside 0-100%
    moisturePercentage = constrain(moisturePercentage, 0, 100);
    
    // Send formatted data
    Serial.print(" MOISTURE:");
    Serial.println(moisturePercentage);
  }
}
