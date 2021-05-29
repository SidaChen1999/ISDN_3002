#include <ESP8266WiFi.h>

#define buttonPin 5
#define LEDPin 16

const int numberPoints = 10;
const int wifis = 16;
// Network information
char* ssid = "ISD_Mesh";
const char* password = "ISDworks!";

const char wifiName1[] = "eduroam";
const char wifiName2[] = "ISD_Mesh";

byte nullMac_byte[6] = {0, 0, 0, 0, 0, 0};
byte target_Mac[6] = {0xd4, 0xad, 0x71, 0x69, 0x60, 0x80};

// ThingSpeak settings
char server[] = "api.thingspeak.com";
String writeAPIKey = "92OSSWMAJMU81FMK";

// Constants
const unsigned long postingInterval = 5L * 1000L;

// Global variables
unsigned long lastConnectionTime = 0;
int measurementNumber = 0;
void setup() {
    Serial.begin(115200);
    pinMode(buttonPin,INPUT);
    pinMode(LEDPin, OUTPUT);
    delay(100);
    Serial.println("Started");
    connectWiFi();
    byte mac[6];
    WiFi.macAddress(mac);
    Serial.print("MAC: ");
    printMacAddress(mac);
    Serial.print("Wifi Mac: ");
    printMacAddress(WiFi.BSSID());
}

void loop(){
    float wifiStrength;
  // In each loop, make sure there is an Internet connection.
    if (WiFi.status() != WL_CONNECTED) { 
        connectWiFi();
    }
    // if (digitalRead(buttonPin) == LOW){
    //     Serial.println(0);
    // }
    // else if (digitalRead(buttonPin) == HIGH) {
    //     Serial.println(1);
    // }
    // If a button press is detected, write the data to ThingSpeak.
    if (digitalRead(buttonPin) == LOW){
        if (millis() - lastConnectionTime > postingInterval) {
            blinkX(2,250); // Verify the button press.
            wifiStrength = getStrength(numberPoints); 
            httpRequest(wifiStrength, measurementNumber);
            blinkX(measurementNumber,200);  // Verify that the httpRequest is complete.
            measurementNumber++;
        }
        
    }
}

void connectWiFi(){
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED){
        Serial.print(".");
        // WiFi.begin(ssid, password);
        delay(500);
    }
    // Display a notification that the connection is successful. 
    Serial.println("Connected");
    // byte bssid[6];
    // memcpy(bssid, WiFi.BSSID(0), sizeof(bssid));
    // Serial.print("bssid: ");
    // printMacAddress(bssid);   
    blinkX(5,50);  
}

void httpRequest(float field1Data, int field2Data) {
    WiFiClient client;
    if (!client.connect(server, 80)){
      
        Serial.println("Connection failed");
        lastConnectionTime = millis();
        client.stop();
        return;     
    }
    else{
        // Create data string to send to ThingSpeak.
        String data = "field1=" + String(field1Data) + "&field2=" + String(field2Data); //shows how to include additional field data in http post
        
        // POST data to ThingSpeak.
        if (client.connect(server, 80)) {
          
            client.println("POST /update HTTP/1.1");
            client.println("Host: api.thingspeak.com");
            client.println("Connection: close");
            client.println("User-Agent: ESP32WiFi/1.1");
            client.println("X-THINGSPEAKAPIKEY: "+writeAPIKey);
            client.println("Content-Type: application/x-www-form-urlencoded");
            client.print("Content-Length: ");
            client.print(data.length());
            client.print("\n\n");
            client.print(data);
            
            Serial.println("RSSI = " + String(field1Data));
            lastConnectionTime = millis();   
            delay(250);
        }
    }
    client.stop();
}

// Take measurements of the Wi-Fi strength and return the average result.
int getStrength(int points){
    long rssi = 0;
    long averageRSSI = 0;
    double mw = 0.0;
    
    for (int i=0 ; i < points; i ++){
        // rssi += WiFi.RSSI();
        long temp = listNetworks();
        if (temp == 0) {
          i --;
        }
        else {
          mw += dbm2Mw(temp);
        }
        
        // Serial.print("RSSI at this time: ");
        // Serial.println(rssi);
        delay(20);
    }
    averageRSSI = mw2Dbm(mw / points);
    Serial.print("average RSSI at this time: ");
    Serial.println(averageRSSI);
    return averageRSSI;
}

// Make the LED blink a variable number of times with a variable delay.
void blinkX(int numTimes, int delayTime){ 
    for (int g = 0; g < numTimes; g ++){
        // Turn the LED on and wait.
        digitalWrite(LEDPin, HIGH);  
        delay(delayTime);
        // Turn the LED off and wait.
        digitalWrite(LEDPin, LOW);
        delay(delayTime);
    }
}

void printMacAddress(byte mac[]) {
  for (int i = 0; i < 6; i ++) {
    if (mac[i] < 16) {
      Serial.print("0");
    }
    Serial.print(mac[i], HEX);
    if (i < 5) {
      Serial.print(":");
    }
  }
  Serial.println();  
}

// int wifiCounter = 0;
long listNetworks(){
//   wifiCounter = 0;
  Serial.println("\nscan start");
  // WiFi.scanNetworks will return the number of networks found
  int n = WiFi.scanNetworks();
  Serial.println("scan done");
  if (n == 0) {
    Serial.println("no networks found");
  } else {
    Serial.print(n);
    Serial.println(" networks found");
    for (int i = 0; i < n; ++i) {
        byte bssid[6];
        memcpy(bssid, WiFi.BSSID(i), sizeof(bssid));
        if (macCompare(bssid, target_Mac)){
            long RSSI = WiFi.RSSI(i);
            Serial.print("RSSI: ");
            Serial.print(RSSI);
            Serial.print("\tMac: ");
            printMacAddress(bssid);
            // return WiFi.RSSI(i);
            return RSSI;
      }

      // Print SSID and RSSI for each network found
    //   Serial.print(i + 1);
    //   Serial.print(": ");
    // //   String SSID = WiFi.SSID(i);
    // //   Serial.print(SSID);
    //   Serial.print(" (");
    //   long RSSI = WiFi.RSSI(i);
    //   Serial.print(RSSI);
    //   Serial.print(")");
    //   Serial.print("\tBSSID: ");
    //   byte bssid[6];
    //   memcpy(bssid, WiFi.BSSID(i), sizeof(bssid));
    //   printMacAddress(bssid);
      
      // Serial.println((WiFi.encryptionType(i) == ENC_TYPE_NONE) ? " " : "*");
      // delay(10);

    //   char SSID2[SSID.length()+1];
    //   SSID.toCharArray(SSID2, SSID.length()+1);
    //   if (wifiCounter == wifis){
    //   }
    //   else if (strcmp(SSID2, wifiName1) == 0 || strcmp(SSID2, wifiName2) == 0){
    //     memcpy(data.BSSIDs[wifiCounter], bssid, sizeof(bssid));
    //     long temp = 0-RSSI;
    //     // Serial.print("temp is ");
    //     data.RSSIs[wifiCounter] = (byte)temp;
    //     wifiCounter ++;
    //     Serial.print("\t(-)");
    //   }
    //   Serial.println();
    }
    return 0;
  }
//   Serial.println("");
//   if (wifiCounter != wifis){
//     for (int i = wifiCounter; i < wifis; i ++){
//       memcpy(data.BSSIDs[i], nullMac_byte, sizeof(nullMac_byte));
//       data.RSSIs[i] = 0;
//     }
//   }
//   return;
}

bool macCompare(byte *mac1, byte *mac2){
    boolean flag = true;
    for(int i = 0; i < 6; i ++) {
        if (mac1[i] != mac2[i]) {
            flag = false;
            break;
        }
    }
    return flag;
}

double dbm2Mw( double dbm )
{
  double mW;
  mW = dbm/10;
  mW = pow( 10.0, mW );
  return mW;
}

double mw2Dbm( double mW )
{
  double dbm;
  dbm = 10*log10(mW);
  return dbm;
}