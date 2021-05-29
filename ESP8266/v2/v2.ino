#include <ESP8266WiFi.h>

#ifndef STASSID
#define STASSID "ISD_Mesh"
#define STAPSK  "ISDworks!"
#endif
#define LEDPIN 16

const int wifis = 16;
const char wifiName1[] = "eduroam";
const char wifiName2[] = "ISD_Mesh";
struct __attribute__((__packed__)) dataPackage {
  byte myMac[6]; 
  byte RSSIs[wifis];
  byte BSSIDs[wifis][6];
} data;
byte outGoing[7 * wifis + 6];

const char* ssid     = STASSID;
const char* password = STAPSK;


const char* host = "192.168.1.107";
const uint16_t port = 65432;

byte nullMac_byte[6] = {0, 0, 0, 0, 0, 0};
WiFiClient client;
int status = WL_IDLE_STATUS;

void setup() {
  Serial.begin(115200);
  pinMode(LEDPIN, OUTPUT);
  WiFi.mode(WIFI_STA);
  connectWiFi();

  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print("MAC: ");
  printMacAddress(mac);
  // *data.myMac = reinterpret_cast<const char*>(mac);
  memcpy(data.myMac, mac, sizeof(mac));
}

int loop_count = 0;

void loop() {
  ledBlink();
  Serial.println("\nScanning available networks...");
  listNetworks(); 
  Serial.println("Communication with server...");
  serverComm();
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

void serverComm(){
  status = WiFi.status();
  if(status != WL_CONNECTED){
    connectWiFi();
  }
  if(!client.connected()){
    connectServer();
  }
  compressData();
  printData();
  Serial.println("sending data to server");
  int sended = client.write(outGoing, 7 * wifis + 6);
  client.flush();
  Serial.print("Sended: ");
  Serial.println(sended);
}

void connectServer(){
  status = WiFi.status();
  if(status != WL_CONNECTED){
    connectWiFi();
  }
  Serial.print("connecting to ");
  Serial.print(host);
  Serial.print(':');
  Serial.println(port);
  if (client.connected()) {
    Serial.println("already connected");
  }
  else if (client.connect(host, port)) {
    Serial.println("connected to server");
  }
  else {
    Serial.println("NOT connected to server");
  }
}

void connectWiFi(){
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  status = WiFi.status();
  int counter = 0;
  while (status != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // WiFi.begin(ssid, password);
    status = WiFi.status();
    counter ++;
    if (counter == 120) {
      WiFi.begin(ssid, password);
      counter = 0;
      Serial.println();
      break;
    }
  }
  Serial.println("WiFi connected");
}

// void connectWiFi(){
//     Serial.println();
//     Serial.print("Connecting to ");
//     Serial.println(ssid);
//     WiFi.begin(ssid, password);
//     while (WiFi.status() != WL_CONNECTED){
//         Serial.print(".");
//         delay(500);
//     }
//     Serial.println("Connected");  
// }

void compressData(){
  memcpy(outGoing, data.myMac, 6);
  memcpy(outGoing+6, data.BSSIDs, wifis * 6);
  memcpy(outGoing+6+wifis*6, data.RSSIs, wifis);
}

void printData(){
  // Serial.println("Printing out data: ");
  Serial.print("My mac: ");
  for (int i = 0; i < 7 * wifis + 6; i ++){
    if (i < (wifis + 1) * 6){
      Serial.print(outGoing[i], HEX);
      Serial.print(" ");
      if ((i+1) % 6 == 0){
        Serial.println();
      }
    }
    else{
      Serial.print(outGoing[i]);
      Serial.print(" ");
    }
  }
  Serial.println();
}

void serverReceive(){
  // wait for data to be available
  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 5000) {
      Serial.println(">>> Client Timeout !");
      client.stop();
      delay(10000);
      return;
    }
  }

  // Read all the lines of the reply from server and print them to Serial
  Serial.println("receiving from remote server");
  // not testing 'client.connected()' since we do not need to send data here
  while (client.available()) {
    char ch = static_cast<char>(client.read());
    Serial.print(ch);
  }
}

void serverClose(){
  // Close the connection
  Serial.println();
  Serial.println("closing connection");
  client.stop();
}

int wifiCounter = 0;
void listNetworks(){
  wifiCounter = 0;
  Serial.println("scan start");
  // WiFi.scanNetworks will return the number of networks found
  int n = WiFi.scanNetworks();
  Serial.println("scan done");
  if (n == 0) {
    Serial.println("no networks found");
  } else {
    Serial.print(n);
    Serial.println(" networks found");
    for (int i = 0; i < n; ++i) {
      // Print SSID and RSSI for each network found
      Serial.print(i + 1);
      Serial.print(": ");
      String SSID = WiFi.SSID(i);
      Serial.print(SSID);
      Serial.print(" (");
      long RSSI = WiFi.RSSI(i);
      Serial.print(RSSI);
      Serial.print(")");
      Serial.print("\tBSSID: ");
      byte bssid[6];
      memcpy(bssid, WiFi.BSSID(i), sizeof(bssid));
      printMacAddress(bssid);
      // Serial.println((WiFi.encryptionType(i) == ENC_TYPE_NONE) ? " " : "*");
      // delay(10);
      
      char SSID2[SSID.length()+1];
      SSID.toCharArray(SSID2, SSID.length()+1);
      if (wifiCounter == wifis){

      }
      else if (strcmp(SSID2, wifiName1) == 0 || strcmp(SSID2, wifiName2) == 0){
        memcpy(data.BSSIDs[wifiCounter], bssid, sizeof(bssid));
        long temp = 0-RSSI;
        // Serial.print("temp is ");
        data.RSSIs[wifiCounter] = (byte)temp;
        wifiCounter ++;
        Serial.print("\t(-)");
      }
      Serial.println();
    }
  }
  Serial.println("");
  if (wifiCounter != wifis){
    for (int i = wifiCounter; i < wifis; i ++){
      memcpy(data.BSSIDs[i], nullMac_byte, sizeof(nullMac_byte));
      data.RSSIs[i] = 0;
    }
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
  // Serial.println();
}
