/**
 * Soil Moisture Sensor Interface
 * 
 * This sketch reads data from a soil moisture sensor and outputs moisture percentage
 * in JSON format. It's designed to be part of a larger smart garden system.
 * 
 * Hardware:
 * - Arduino board
 * - Soil moisture sensor connected to analog pin A0
 */

// Define the analog pin where the soil moisture sensor is connected
const int moistureSensorPin = A0;

// Set the interval between readings (5 seconds = 5000 milliseconds)
const long interval = 5000;

// Variable to store the last time a measurement was taken
unsigned long previousMillis = 0;

// Calibration values
int airValue = 669;    // Value in air (completely dry) - adjust this!
int waterValue = 202;  // Value in water (completely wet) - adjust this!

/**
 * Initial setup function - runs once when Arduino starts or resets
 */
void setup() {
  // Initialize serial communication at 9600 bits per second
  Serial.begin(9600);
  
  // Set moisture sensor pin as INPUT
  pinMode(moistureSensorPin, INPUT);
}

/**
 * Main loop function - runs repeatedly after setup
 */
void loop() {
  // Get current time in milliseconds since Arduino started
  unsigned long currentMillis = millis();
  
  // Check if it's time to take a new reading (based on interval)
  if (currentMillis - previousMillis >= interval) {
    // Save the current time as the last reading time
    previousMillis = currentMillis;
    
    // Read the analog value from the moisture sensor
    int sensorValue = analogRead(moistureSensorPin);
    
    // Convert the raw sensor value to a moisture percentage
    // map(value, fromLow, fromHigh, toLow, toHigh)
    // Note: The sensor gives lower values when wet, higher when dry
    int moisturePercentage = map(sensorValue, airValue, waterValue, 0, 100);
    
    // Ensure the percentage stays within valid range (0-100%)
    moisturePercentage = constrain(moisturePercentage, 0, 100);
    
    // Output the moisture percentage in JSON format for easy parsing
    // by the larger smart garden system
    Serial.print("{\"moisture\":");
    Serial.print(moisturePercentage);
    Serial.println("}");
  }
}
