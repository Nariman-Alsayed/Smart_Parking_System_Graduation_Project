#include <stdint.h>
#include <WiFi.h>
#include <SimpleBLE.h>

SimpleBLE ble;

const char* ssid     = "WE_E66D88";
const char* password = "jbn16065";
const char* httpHost = "192.168.1.3";
const uint16_t httpPort = 9999;

char entryUrlPath[] = "/smartparking/api/slotEntry.php?slot_number=0";
char exitUrlPath[] = "/smartparking/api/slotExit.php?slot_number=0";

uint8_t trigPins[] = { 26, 15, 27, 4};
uint8_t echoPins[] = { 36, 39, 34, 35 };
uint8_t ledPins[] = {2,2,2,2};
uint8_t i;
#define SensorCount sizeof(echoPins)
 
bool lastSlotState[SensorCount] = { 0 };


void setup() {
    Serial.begin(115200);

    ble.begin("slot 1-4");

    for(i = 0; i < SensorCount; i++) {
      pinMode(trigPins[i], OUTPUT);
      pinMode(echoPins[i], INPUT);
      pinMode(ledPins[i], OUTPUT);
    }

    Serial.print("Connecting to ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
  for(i = 0; i < SensorCount; i++) {
    float d;
    bool slotEmpty = 0;

    digitalWrite(trigPins[i], HIGH);
    delay(1);
    digitalWrite(trigPins[i], LOW);
    noInterrupts();
    d = pulseIn(echoPins[i], HIGH, 23529.4);
    interrupts();
    d /= 58.8235;
    slotEmpty = d > 100;
    digitalWrite(ledPins[i], slotEmpty ? HIGH : LOW);
    
    Serial.print("Slot ");
    Serial.print(i);
    Serial.println(":");
    Serial.print("D ");
    Serial.print(d);
    Serial.print("\tStatus: ");
    Serial.println(lastSlotState[i] ? "Empty" : "Full");
    if(slotEmpty != lastSlotState[i]) {
      // select the correct url depending on the event (entry or exit)
      char *path = slotEmpty ? exitUrlPath : entryUrlPath;
      // get the selected url length
      char pathLen = slotEmpty ? sizeof(exitUrlPath) - 1 : sizeof(entryUrlPath) - 1;
      // modify the last character in the url (which is the slot number)
      // by adding the integer value of the slot number to the character value 0
      // which effectively gives us a character that represents the slot number
      path[pathLen - 1] = '0' + i;

      Serial.print("Updating status to: ");
      Serial.println(slotEmpty ? "Empty" : "Full");

      if(sendSlotStatus(httpHost, httpPort, path)) {
        lastSlotState[i] = slotEmpty;
      }
    }

    Serial.println();
    delay(250);
  }

//  delay(10000);
}

bool sendSlotStatus(const char* httpHost, uint16_t httpPort,const char* url) {
  WiFiClient client;

  if (!client.connect(httpHost, httpPort)) {
      Serial.println("connection failed");
      return false;
  }

  Serial.print("Requesting URL: ");
  Serial.println(url);

  // send the request to the server
  client.print(String("GET ") + url + " HTTP/1.1\r\n"
                + "Host:" + httpHost + "\r\n"
                + "Connection: close\r\n\r\n");

//  uintmax_t timeout = millis();

//  while(client.available()) {
//    if (millis() - timeout > 5000) {
//        Serial.println(">>> Client Timeout !");
//        client.stop();
//        return false;
//    }
//  }
  delay(5000);

  // Read all the lines of the reply from server and print them to Serial
  Serial.println("Server Reponse:");
  while(client.available()) {
      String line = client.readStringUntil('\r');
      Serial.print(line);
  }
  
  client.stop();

  return true;
}
