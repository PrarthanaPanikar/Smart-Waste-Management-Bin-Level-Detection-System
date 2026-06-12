/**
 * Smart Waste Management & Bin Level Detection System
 * ESP32 Firmware
 * 
 * Hardware:
 * - ESP32 NodeMCU
 * - HC-SR04 Ultrasonic Sensor
 * - DHT11 Temperature & Humidity Sensor (Optional)
 * - MQ-135 Gas Sensor (Optional)
 * - Active Buzzer
 * - 3x Status LEDs (Green, Yellow, Red)
 * 
 * Library Dependencies (Install via Library Manager):
 * - PubSubClient by Nick O'Leary
 * - DHT sensor library by Adafruit
 * - Adafruit Unified Sensor by Adafruit
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

// --- Hardware Pin Definitions ---
#define PIN_TRIG 5
#define PIN_ECHO 18
#define PIN_DHT 4
#define PIN_MQ135 34
#define PIN_BUZZER 12
#define PIN_LED_GREEN 14
#define PIN_LED_YELLOW 27
#define PIN_LED_RED 26

// --- Sensor Settings ---
#define DHTTYPE DHT11
DHT dht(PIN_DHT, DHTTYPE);

const float BIN_DEPTH_CM = 30.0; // Total height of the bin from sensor to bottom (calibrate as needed)
const float FULL_THRESHOLD_CM = 5.0; // Distance at which bin is considered 100% full

// --- Wi-Fi & MQTT Configuration ---
const char* ssid = "Your_SSID";           // Replace with your Wi-Fi SSID
const char* password = "Your_Password";   // Replace with your Wi-Fi Password
const char* mqtt_server = "broker.hivemq.com"; // Public MQTT Broker
const int mqtt_port = 1883;
const char* client_id = "SmartWasteBin_Node1";

WiFiClient espClient;
PubSubClient client(espClient);

// Timing variables
unsigned long lastMsgTime = 0;
const long intervalMs = 5000; // Publish interval (5 seconds)

// --- Helper Functions ---

// Connect to Wi-Fi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to Wi-Fi SSID: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Wi-Fi connected successfully!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// Reconnect to MQTT Broker
void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(client_id)) {
      Serial.println("connected");
      // Subscribe to topics here if we want to receive commands
      // client.subscribe("smartbin/node1/cmd");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// Read Distance from HC-SR04 Ultrasonic Sensor
float readDistance() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  
  long duration = pulseIn(PIN_ECHO, HIGH, 30000); // 30ms timeout
  if (duration == 0) {
    return -1.0; // Timeout or sensor issue
  }
  
  // Speed of sound: 343 m/s = 0.0343 cm/us
  float distance = (duration * 0.0343) / 2.0;
  return distance;
}

// Update local indicators (LEDs and Buzzer)
void updateIndicators(float fillPercentage) {
  if (fillPercentage < 0.0) {
    // Sensor error: Blink all LEDs as a warning
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_YELLOW, HIGH);
    digitalWrite(PIN_LED_RED, HIGH);
    return;
  }

  if (fillPercentage < 50.0) {
    // Empty / Low Level (Green)
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
  } 
  else if (fillPercentage >= 50.0 && fillPercentage < 80.0) {
    // Half-Full Level (Yellow)
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, HIGH);
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
  } 
  else {
    // Full / Critical Level (Red + Buzzer alarm)
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, HIGH);
    
    // Buzz alert
    digitalWrite(PIN_BUZZER, HIGH);
    delay(200);
    digitalWrite(PIN_BUZZER, LOW);
  }
}

// --- Arduino Setup and Loop ---

void setup() {
  Serial.begin(115200);
  
  // Pins Configuration
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_MQ135, INPUT);

  // Turn off indicators initially
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_YELLOW, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  // Initialize DHT Sensor
  dht.begin();

  // Configure MQTT
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsgTime > intervalMs) {
    lastMsgTime = now;

    // 1. Measure Distance & Compute Level
    float distance = readDistance();
    float fillPercentage = 0.0;
    String status = "Unknown";

    if (distance >= 0.0) {
      // Constrain distance to range
      float adjustedDistance = distance;
      if (adjustedDistance > BIN_DEPTH_CM) adjustedDistance = BIN_DEPTH_CM;
      if (adjustedDistance < FULL_THRESHOLD_CM) adjustedDistance = FULL_THRESHOLD_CM;

      // Calculate fill level percentage
      fillPercentage = ((BIN_DEPTH_CM - adjustedDistance) / (BIN_DEPTH_CM - FULL_THRESHOLD_CM)) * 100.0;
      
      if (fillPercentage < 50.0) {
        status = "Empty";
      } else if (fillPercentage >= 50.0 && fillPercentage < 80.0) {
        status = "Half Full";
      } else {
        status = "Full";
      }
    } else {
      Serial.println("Error reading ultrasonic sensor!");
      status = "Error";
    }

    // 2. Read environmental sensors
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    if (isnan(temperature)) temperature = 0.0;
    if (isnan(humidity)) humidity = 0.0;

    // Read analog MQ-135 sensor (0 - 4095)
    int gasRaw = analogRead(PIN_MQ135);
    float gasPpm = (gasRaw / 4095.0) * 100.0; // Scaled to a percentage for simplicity

    // 3. Update Local Indicators
    updateIndicators(fillPercentage);

    // 4. Print telemetry to Serial Monitor
    Serial.printf("Distance: %.2f cm | Fill: %.1f%% | Status: %s | Temp: %.1fC | Hum: %.1f%% | Gas: %.1f%%\n",
                  distance, fillPercentage, status.c_str(), temperature, humidity, gasPpm);

    // 5. Construct JSON Payload and Publish to MQTT
    char payload[256];
    snprintf(payload, sizeof(payload),
             "{\"bin_id\":\"bin_node_1\",\"distance\":%.1f,\"fill_percentage\":%.1f,\"status\":\"%s\",\"temp\":%.1f,\"humidity\":%.1f,\"gas_level\":%.1f}",
             distance, fillPercentage, status.c_str(), temperature, humidity, gasPpm);

    // Publish to telemetry topic
    client.publish("smartbin/node1/data", payload);

    // Publish direct alert when full
    if (fillPercentage >= 80.0) {
      char alertPayload[128];
      snprintf(alertPayload, sizeof(alertPayload), "{\"bin_id\":\"bin_node_1\",\"alert\":\"Bin Nearly Full! Please Dispatch Pickup.\",\"fill_percentage\":%.1f}", fillPercentage);
      client.publish("smartbin/node1/alert", alertPayload);
    }
  }
}

/* 
 * NOTE: For long-term battery deployment, deep sleep should be used.
 * You can replace the standard loop with:
 * 
 * void enterDeepSleep() {
 *   Serial.println("Entering deep sleep for 15 minutes...");
 *   esp_sleep_enable_timer_wakeup(15ULL * 60ULL * 1000000ULL); // 15 mins in microseconds
 *   esp_deep_sleep_start();
 * }
 */
