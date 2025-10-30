import sounddevice as sd
import queue
import json
import requests
from vosk import Model, KaldiRecognizer
import re

# --- Configurações ---
ESP_IP = "http://192.168.4.1"  # IP do ESP32 (modo AP)
MODEL_PATH = "vosk-model-small-pt-0.3"  # Caminho do modelo offline

# --- Inicializa o modelo ---
print("🔧 Carregando modelo de voz offline...")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)
print("✅ Modelo carregado com sucesso!\n")

# --- Fila de áudio ---
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# --- Função de envio HTTP ---
def enviar(cmd):
    try:
        r = requests.get(f"{ESP_IP}/acao?cmd={cmd}", timeout=3)
        print("✅", r.text)
    except Exception as e:
        print("❌ Erro ao conectar ao ESP32:", e)

# --- Função principal de interpretação ---
def interpretar(frase):
    frase_original = frase.strip().lower()
    frase = frase_original

    # Remover acentos e normalizar
    frase = re.sub(r"[áàãâ]", "a", frase)
    frase = re.sub(r"[éèê]", "e", frase)
    frase = re.sub(r"[íìî]", "i", frase)
    frase = re.sub(r"[óòõô]", "o", frase)
    frase = re.sub(r"[úùû]", "u", frase)

    # Converter números por extenso
    frase = frase.replace("um", "1").replace("uma", "1")
    frase = frase.replace("dois", "2").replace("duas", "2")
    frase = frase.replace("tres", "3").replace("três", "3")

    print(f"📢 Você disse: {frase_original}")

    # --- Identificar tipo de ação ---
    acao = None
    if any(p in frase for p in ["desligar", "apagar", "desativa", "desconectar"]):
        acao = "desligar"
    elif any(p in frase for p in ["ligar", "acender", "ativa", "conectar"]):
        acao = "ligar"

    if not acao:
        print("🤔 Nenhuma ação (ligar/desligar) reconhecida.")
        return

    # --- Identificar alvo ---
    alvo = None
    numero = None

    # luzes
    if any(p in frase for p in ["luz", "lampada", "luzes"]):
        alvo = "luz"
        # Detectar número se existir
        for n in ["1", "2", "3"]:
            if f" {n}" in frase:
                numero = n
                break

    # ventoinha / ventilador
    elif any(p in frase for p in ["ventoinha", "ventilador"]):
        alvo = "fan"

    # todos
    elif any(p in frase for p in ["tudo", "todas", "geral"]):
        alvo = "todas"

    # --- Executar ação conforme o alvo ---
    if alvo == "luz" and numero:
        enviar(f"{acao}_led{numero}")
    elif alvo == "luz" and not numero:
        # se disser "ligar luzes" sem número
        for i in range(1, 4):
            enviar(f"{acao}_led{i}")
    elif alvo == "fan":
        enviar(f"{acao}_fan1")
    elif alvo == "todas":
        for i in range(1, 4):
            enviar(f"{acao}_led{i}")
        enviar(f"{acao}_fan1")
    else:
        print("🤔 Comando não reconhecido.")

# --- Captura de áudio contínua ---
print("🎙️ Fale um comando como 'ligar luz 1' ou 'desligar ventoinha' (Ctrl+C para sair)\n")

with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                       channels=1, callback=audio_callback):

    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            text = json.loads(result)["text"]
            if text:
                interpretar(text)
