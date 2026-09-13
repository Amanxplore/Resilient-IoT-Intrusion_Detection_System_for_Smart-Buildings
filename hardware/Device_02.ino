#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include <time.h>

// ------------------- SENSOR -------------------
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ------------------- WIFI -------------------
const char* ssid = "Powerhouse";
const char* password = "$$$$$$$$"; // Replace with your WiFi password

// ------------------- MQTT -------------------
const char* mqtt_server = "192.168.1.8";  // YOUR LAPTOP IP (SYPHER)
const int mqtt_port = 1883;
WiFiClient espClient;
PubSubClient client(espClient);

// ------------------- DEVICE -------------------
String device_id = "Device_02";

// ------------------- TIME -------------------
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

// ------------------- FUNCTIONS -------------------
void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("ESP8266 IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  int attempts = 0;
  while (!client.connected() && attempts < 5) {
    Serial.print("Connecting to MQTT broker at ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.println(mqtt_port);
    
    if (client.connect(device_id.c_str())) {
      Serial.println("MQTT connected successfully!");
    } else {
      Serial.print("MQTT connection failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds...");
      attempts++;
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\nStarting ESP8266...");
  
  dht.begin();
  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);
  client.setKeepAlive(30);  // Keep connection alive every 30 seconds
  
  // NTP time setup
  configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org");
  
  int timeAttempts = 0;
  while (time(nullptr) < 100000 && timeAttempts < 20) {
    delay(500);
    Serial.print(".");
    timeAttempts++;
  }
  Serial.println("\nTime synced");
}

void loop() {
  // Keep MQTT connection alive - THIS WAS MISSING
  if (!client.connected()) {
    reconnect();
  }
  client.loop();  // CRITICAL: Processes MQTT messages and keeps connection alive
  
  // Wait 5 seconds between readings
  delay(5000);
  
  // Read sensor
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  if (isnan(h) || isnan(t)) {
    Serial.println("Sensor error - check wiring!");
    return;
  }
  
  // Get time
  time_t now = time(nullptr);
  struct tm* timeInfo = localtime(&now);
  
  char timeString[25];
  strftime(timeString, sizeof(timeString), "%d-%m-%Y %H:%M:%S", timeInfo);
  
  // Sequence counter for replay protection
  static uint32_t seq_num = 0;
  seq_num++;

  // Create JSON payload
  String payload = "{";
  payload += "\"device\":\"" + device_id + "\",";
  payload += "\"seq\":" + String(seq_num) + ",";
  payload += "\"time\":\"" + String(timeString) + "\",";
  payload += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  payload += "\"temp\":" + String(t, 1) + ",";
  payload += "\"humidity\":" + String(h, 1);
  payload += "}";

  
  // Publish to topic
  String topic = "sensor/" + device_id;
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.print("✓ Published to ");
    Serial.print(topic);
    Serial.print(": ");
    Serial.println(payload);
  } else {
    Serial.println("✗ Failed to publish!");
  }
}
