/*
  This example  prints the board's MAC address, and
  scans for available WiFi networks using the NINA module.
  Every ten seconds, it scans again. It doesn't actually
  connect to any network, so no encryption scheme is specified.
  BSSID and WiFi channel are printed

  Circuit:
    Board with NINA module (Arduino MKR WiFi 1010, MKR VIDOR 4000 and UNO WiFi Rev.2)

  This example is based on ScanNetworks

  created 1 Mar 2017
  by Arturo Guadalupi
*/


#include <SPI.h>
#include <WiFiNINA.h>
#include "arduino_secrets.h" 
// #include "ESP8266WiFi.h"
// #include <string>

struct __attribute__((__packed__)) dataPackage {
  byte myMac[6]; 
  byte RSSIs[6];
  byte BSSIDs[6][6];
} data;
byte outGoing[48];

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)
int keyIndex = 0;            // your network key index number (needed only for WEP)

int status = WL_IDLE_STATUS;
// if you don't want to use DNS (and reduce your sketch size)
// use the numeric IP instead of the name for the server:
//IPAddress server(142.250.204.46);  // numeric IP for Google (no DNS)
char server[] = "192.168.1.107"; //"www.google.com"; //192.168.1.107    // name address for Google (using DNS)
int port = 65432;

// Initialize the Ethernet client library
// with the IP address and port of the server
// that you want to connect to (port 80 is default for HTTP):
WiFiClient client;

char nullMac[12] = {'0','0','0','0','0','0','0','0','0','0','0','0'};
byte nullMac_byte[6] = {0, 0, 0, 0, 0, 0};

void setup() {
  //Initialize serial and wait for port to open:
  Serial.begin(115200);
  pinMode(13, OUTPUT);

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }
  delay(1000);

  // print your MAC address:
  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print("MAC: ");
  printMacAddress(mac);
  // *data.myMac = reinterpret_cast<const char*>(mac);
  memcpy(data.myMac, mac, sizeof(mac));

  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);

    // wait 1 seconds for connection:
    delay(1000);
  }

  Serial.println("\nStarting connection to server...");
  // if you get a connection, report back via serial:
  if (client.connect(server, port)) {
    Serial.println("Connected to server");
    // Make a HTTP request:
    // client.print(data.myMac);
    // client.println("Connection: close");
    // client.println();
  }
  delay(1000);
  // String c;
  // while (client.available()) {
  //   c += (client.read());
  // }
  // Serial.println(c);
  
}

int loop_count = 0;

void loop() {
  ledBlink(loop_count);
  loop_count++;
  // scan for existing networks:
  Serial.println("Scanning available networks...");
  listNetworks(); 
  connectWiFi();
  Serial.println("Communication with server...");
  serverComm();
}

int wifiCounter = 0;
void listNetworks() {
  wifiCounter = 0;
  // scan for nearby networks:
  Serial.println("** Scan Networks **");
  int numSsid = WiFi.scanNetworks();
  if (numSsid == -1)
  {
    Serial.println("Couldn't get a WiFi connection");
    return;
  }

  // print the list of networks seen:
  Serial.print("number of available networks: ");
  Serial.println(numSsid);

  // print the network number and name for each network found:
  for (int thisNet = 0; thisNet < numSsid; thisNet++) {
    Serial.print(thisNet + 1);
    Serial.print(") ");
    // SSID
    Serial.print("SSID: ");
    String SSID = WiFi.SSID(thisNet);
    Serial.print(SSID);
    // Signal Strength
    Serial.print("\tSignal: ");
    long RSSI = WiFi.RSSI(thisNet);
    Serial.print(RSSI);
    Serial.print(" dBm");
    // Channel
    // Serial.print("\tChannel: ");
    // Serial.print(WiFi.channel(thisNet));
    // BSSID
    byte bssid[6];
    Serial.print("\t\tBSSID: ");
    printMacAddress(WiFi.BSSID(thisNet, bssid));
    // Encryption
    // Serial.print("\tEncryption: ");
    // printEncryptionType(WiFi.encryptionType(thisNet));
    Serial.flush();

    char SSID2[SSID.length()+1];
    SSID.toCharArray(SSID2, SSID.length()+1);
    if (strcmp(SSID2, "ISD_Mesh") == 0){
      memcpy(data.BSSIDs[wifiCounter], bssid, sizeof(bssid));
      long temp = 0-RSSI;
      // Serial.print("temp is ");
      // Serial.println(temp);
      data.RSSIs[wifiCounter] = (byte)temp;
      wifiCounter ++;
    }
  }
  Serial.println();
  if (wifiCounter != 6){
    for (int i = wifiCounter; i < 6; i ++){
      memcpy(data.BSSIDs[i], nullMac_byte, sizeof(nullMac_byte));
      data.RSSIs[i] = 0;
    }
  }
}

void ledBlink(int count){
  if (count % 2 == 0)
  {
    digitalWrite(13, HIGH);
  }
  else
  {
    digitalWrite(13, LOW);
  }
}

void printEncryptionType(int thisType) {
  // read the encryption type and print out the name:
  switch (thisType) {
    case ENC_TYPE_WEP:
      Serial.print("WEP");
      break;
    case ENC_TYPE_TKIP:
      Serial.print("WPA");
      break;
    case ENC_TYPE_CCMP:
      Serial.print("WPA2");
      break;
    case ENC_TYPE_NONE:
      Serial.print("None");
      break;
    case ENC_TYPE_AUTO:
      Serial.print("Auto");
      break;
    case ENC_TYPE_UNKNOWN:
    default:
      Serial.print("Unknown");
      break;
  }
}

void print2Digits(byte thisByte) {
  if (thisByte < 0xF) {
    Serial.print("0");
  }
  Serial.print(thisByte, HEX);
}

void printMacAddress(byte mac[]) {
  for (int i = 5; i >= 0; i--) {
    if (mac[i] < 16) {
      Serial.print("0");
    }
    Serial.print(mac[i], HEX);
    if (i > 0) {
      Serial.print(":");
    }
  }
  Serial.println();
}

void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}

void serverComm(){
  if (!client.connected()) {
    connectServer();
  }
  compressData();
  printData();
  int sended = client.write(outGoing, 48);
  client.flush();
  // Serial.print("sended in byte: ");
  // Serial.println(sended);
}

void connectWiFi(){
  status = WiFi.status();
  Serial.print("Attempting to connect to SSID: ");
  Serial.println(ssid);
  while (status != WL_CONNECTED) {
    Serial.print(".");
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);

    // wait 1 seconds for connection:
    delay(1000);
  }
  Serial.println("Connected to WiFi");
}

void connectServer(){
  // Serial.println("Starting connection to server...");
  // if you get a connection, report back via serial:
  if (client.connected()){
    Serial.println("already connected");
  }
  else if (client.connect(server, port)) {
    Serial.println("connected to server");
  }
  else {
    Serial.println("NOT connected to server");
  }
}

void compressData(){
  memcpy(outGoing, data.myMac, 6);
  memcpy(outGoing+6, data.BSSIDs, 36);
  memcpy(outGoing+42, data.RSSIs, 6);
}

void printData(){
  Serial.println("Printing out data: ");
  
  for (int i = 0; i < 48; i ++){
    if (i < 42){
      Serial.print(outGoing[i], HEX);
    }
    else{
      Serial.print(outGoing[i]);
    }
    
    Serial.print(" ");
    if ((i+1) % 6 == 0){
      Serial.println();
    }
  }
}
