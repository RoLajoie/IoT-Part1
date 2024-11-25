#include <WiFi.h>
#include <WiFiMulti.h>
#include <PubSubClient.h>

#include <SPI.h>
#include <MFRC522.h>
// Define pins for RFID
#define SS_PIN 5 // SDA Pin on RC522
#define RST_PIN 4 // RST Pin on RC522
MFRC522 rfid(SS_PIN, RST_PIN); // Create MFRC522 instance
WiFiMulti WiFiMulti;

// Define the pin for the photoresistor
const int photoresistorPin = 32; // Analog pin
const char* mqtt_server = "192.168.101.131";

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  Serial.println();
  Serial.print("Waiting for WiFi... ");
  while (WiFiMulti.run() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(String topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
  }
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("vanieriot")) {
      Serial.println("connected");
      client.subscribe("home/light");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(10);

  WiFiMulti.addAP("Willynilly", "segregation");
  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  SPI.begin(); // Initialize SPI bus
rfid.PCD_Init(); // Initialize MFRC522 reader
Serial.println("Place your RFID card near the reader...");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Read the value from the photoresistor
  int lightValue = analogRead(photoresistorPin);

  // Convert the light intensity value to a string
  char message[10]; // Allocate enough space for the number
  snprintf(message, sizeof(message), "%d", lightValue);

  // Print the light intensity to the serial monitor
  Serial.println(message);

  // Publish the light intensity to the MQTT topic
  client.publish("home/light", message);

  // Delay between readings
  delay(2000); // Adjust the delay as needed

  // Look for new cards
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Create a string to store the UID
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uid += "0"; // Add leading zero for single-digit bytes
    }
    uid += String(rfid.uid.uidByte[i], HEX);
  }

  // Print UID to serial monitor
  Serial.print("Card UID: ");
  Serial.println(uid);

  // Publish the UID as the message to the MQTT topic
  client.publish("home/rfid", uid.c_str());

  // Halt PICC
  rfid.PICC_HaltA();
}
