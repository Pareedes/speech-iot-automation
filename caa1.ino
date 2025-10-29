#include <WiFi.h>
#include <WebServer.h>

// --- Configurações da Rede que o ESP32 vai criar ---
const char* ssid = "Bancada"; // Nome da rede Wi-Fi que o ESP32 criará
const char* password = "senha12345"; // Senha para a rede. Mínimo 8 caracteres.

// --- Definição dos Pinos ---
const int ledPin1 = 25;
const int ledPin2 = 26;
const int ledPin3 = 27;
const int fanPin1 = 18;
const int fanPin2 = 19;

// --- Configurações de relé ativo LOW ---
const int RELAY_ON  = LOW;
const int RELAY_OFF = HIGH;

// --- Criação do servidor web ---
WebServer server(80);

void handleRoot() {
  server.send(200, "text/plain", "Servidor da Bancada Ativo! IP: 192.168.4.1");
}

void handleAcao() {
  if (!server.hasArg("cmd")) {
    server.send(400, "text/plain", "Erro: comando nao recebido");
    return;
  }

  String comando = server.arg("cmd");
  comando.toLowerCase();

  if (comando == "ligar_led1") digitalWrite(ledPin1, HIGH);
  else if (comando == "desligar_led1") digitalWrite(ledPin1, LOW);
  else if (comando == "ligar_led2") digitalWrite(ledPin2, HIGH);
  else if (comando == "desligar_led2") digitalWrite(ledPin2, LOW);
  else if (comando == "ligar_led3") digitalWrite(ledPin3, HIGH);
  else if (comando == "desligar_led3") digitalWrite(ledPin3, LOW);
  else if (comando == "ligar_fan1") digitalWrite(fanPin1, RELAY_ON);
  else if (comando == "desligar_fan1") digitalWrite(fanPin1, RELAY_OFF);
  else if (comando == "ligar_fan2") digitalWrite(fanPin2, RELAY_ON);
  else if (comando == "desligar_fan2") digitalWrite(fanPin2, RELAY_OFF);
  else {
    server.send(400, "text/plain", "Comando desconhecido");
    return;
  }

  server.send(200, "text/plain", "Comando executado: " + comando);
  Serial.println("Executado: " + comando);
}

void setup() {
  Serial.begin(115220);

  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(ledPin3, OUTPUT);
  pinMode(fanPin1, OUTPUT);
  pinMode(fanPin2, OUTPUT);

  digitalWrite(ledPin1, LOW);
  digitalWrite(ledPin2, LOW);
  digitalWrite(ledPin3, LOW);
  digitalWrite(fanPin1, RELAY_OFF);
  digitalWrite(fanPin2, RELAY_OFF);

  Serial.println("Configurando o ESP32 como Ponto de Acesso (AP)...");
  
  // Inicia o ESP32 no modo Access Point
  WiFi.softAP(ssid, password);

  IPAddress myIP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(myIP); // Imprime o IP do ESP32 (será 192.168.4.1)

  server.on("/", handleRoot);
  server.on("/acao", handleAcao);
  server.begin();
  Serial.println("Servidor iniciado!");
}

void loop() {
  server.handleClient();
}