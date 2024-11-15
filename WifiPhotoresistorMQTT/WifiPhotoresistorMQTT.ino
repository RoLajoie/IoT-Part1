#include <WiFi.h>
#include <WiFiMulti.h>
#include <PubSubClient.h>

WiFiMulti WiFiMulti;

// Define the pin for the photoresistor
const int photoresistorPin = 32; // Analog pin
const char* mqtt_server = "YOUR_MQTT_BROKER_IP_ADDRESS";

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
      client.subscribe("room/light");
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

  WiFiMulti.addAP("REPLACE_WITH_YOUR_SSID", "REPLACE_WITH_YOUR_PASSWORD");
  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
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
  client.publish("room/light_intensity", message);

  // Delay between readings
  delay(2000); // Adjust the delay as needed
}
