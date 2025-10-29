import {
  WebSocketGateway,
  WebSocketServer,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { WebSocket } from 'ws';
import axios from 'axios'; // <--- IMPORTANTE: instale axios com "npm i axios"

@WebSocketGateway({ path: '/speech-recognition' })
export class AppSpeechRecognitionGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: any;

  // 🧠 Endereço base do seu ESP32
  private espBaseUrl = process.env.ESP_URL || 'http://192.168.43.120';
  // ↑ Troque esse IP pelo que aparece no Serial Monitor do seu ESP32.

  handleConnection(client: WebSocket) {
    console.log('✅ Client connected');
    client.send(JSON.stringify({ message: 'Connected to NestJS backend' }));

    // Ouvindo mensagens recebidas do app Flutter
    client.on('message', async (raw) => {
      try {
        const message = JSON.parse(raw.toString());
        console.log('📩 Received message from app:', message);
        await this.handleMessage(client, message);
      } catch (err) {
        console.error('❌ Error parsing message:', err);
        client.send(JSON.stringify({ error: 'Invalid message format' }));
      }
    });
  }

  handleDisconnect() {
    console.log('❎ Client disconnected');
  }

  // 🔁 Processa o texto reconhecido e envia comando ao ESP32
  private async handleMessage(client: WebSocket, data: any) {
    try {
      console.log('🔍 Processing:', data);

      // 1️⃣ Extrair texto do JSON recebido
      const payload = typeof data === 'string' ? JSON.parse(data) : data;
      const best =
        payload.words && payload.words[0] && payload.words[0].words
          ? payload.words[0].words
          : null;

      if (!best) {
        client.send(JSON.stringify({ error: 'No recognized words' }));
        return;
      }

      const text = best.toLowerCase();
      console.log('🗣️ Recognized text:', text);

      // 2️⃣ Mapear frases de voz para comandos do ESP
      let cmd: string | null = null;

      if (text.includes('ligar') && text.includes('ventoinha')) cmd = 'ligar_fan1';
      else if (text.includes('desligar') && text.includes('ventoinha')) cmd = 'desligar_fan1';
      else if (text.includes('ligar') && text.includes('led 1')) cmd = 'ligar_led1';
      else if (text.includes('desligar') && text.includes('led 1')) cmd = 'desligar_led1';
      else if (text.includes('ligar') && text.includes('led 2')) cmd = 'ligar_led2';
      else if (text.includes('desligar') && text.includes('led 2')) cmd = 'desligar_led2';
      else if (text.includes('ligar') && text.includes('led 3')) cmd = 'ligar_led3';
      else if (text.includes('desligar') && text.includes('led 3')) cmd = 'desligar_led3';

      if (!cmd) {
        client.send(
          JSON.stringify({
            message: 'No mapped command for recognized text',
            recognized: text,
          }),
        );
        return;
      }

      // 3️⃣ Enviar comando ao ESP via HTTP
      const espUrl = `${this.espBaseUrl}/acao?cmd=${encodeURIComponent(cmd)}`;
      console.log('🌐 Sending to ESP:', espUrl);

      const response = await axios.get(espUrl, { timeout: 4000 });

      console.log('✅ ESP response:', response.status, response.data);
      client.send(
        JSON.stringify({
          message: 'Command forwarded to ESP',
          cmd,
          espResponse: response.data,
        }),
      );
    } catch (err: any) {
      console.error('⚠️ Error handling message:', err.message);
      client.send(JSON.stringify({ error: String(err) }));
    }
  }
}
