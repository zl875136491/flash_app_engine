/** FunASR WebSocket 实时转写（PCM16 / 16kHz / mono）。 */

export type FunAsrStatus = "idle" | "connecting" | "listening" | "error";

export type FunAsrHandlers = {
  onPartial?: (text: string) => void;
  onStatus?: (status: FunAsrStatus) => void;
  onError?: (message: string) => void;
};

function floatTo16BitPCM(input: Float32Array): Int16Array {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    const s = Math.max(-1, Math.min(1, input[i] ?? 0));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output;
}

function downsampleBuffer(
  buffer: Float32Array,
  sampleRate: number,
  targetRate: number,
): Float32Array {
  if (targetRate === sampleRate) return buffer;
  const ratio = sampleRate / targetRate;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);
  for (let i = 0; i < newLength; i += 1) {
    const start = Math.floor(i * ratio);
    const end = Math.min(Math.floor((i + 1) * ratio), buffer.length);
    let sum = 0;
    let count = 0;
    for (let j = start; j < end; j += 1) {
      sum += buffer[j] ?? 0;
      count += 1;
    }
    result[i] = count > 0 ? sum / count : 0;
  }
  return result;
}

export function getFunAsrWsUrl(): string {
  return import.meta.env.VITE_FUNASR_WS_URL || "ws://10.17.150.235:10095";
}

export class FunAsrSession {
  private ws: WebSocket | null = null;
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private handlers: FunAsrHandlers;
  private closed = false;

  constructor(handlers: FunAsrHandlers = {}) {
    this.handlers = handlers;
  }

  async start(): Promise<void> {
    this.closed = false;
    this.handlers.onStatus?.("connecting");

    const wsUrl = getFunAsrWsUrl();
    this.ws = new WebSocket(wsUrl);
    this.ws.binaryType = "arraybuffer";

    await new Promise<void>((resolve, reject) => {
      if (!this.ws) return reject(new Error("WebSocket 未创建"));
      const timer = window.setTimeout(() => {
        reject(new Error("FunASR 连接超时"));
      }, 8000);
      this.ws.onopen = () => {
        window.clearTimeout(timer);
        resolve();
      };
      this.ws.onerror = () => {
        window.clearTimeout(timer);
        reject(new Error("无法连接 FunASR，可改为手动输入需求"));
      };
    });

    this.ws.onmessage = (event) => {
      try {
        const raw = typeof event.data === "string" ? event.data : "";
        if (!raw) return;
        const data = JSON.parse(raw) as { text?: string };
        if (data.text) this.handlers.onPartial?.(data.text);
      } catch {
        // ignore non-json
      }
    };

    this.ws.onclose = () => {
      if (!this.closed) {
        this.handlers.onStatus?.("error");
        this.handlers.onError?.("语音识别连接已断开");
      }
    };

    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
      video: false,
    });

    this.audioContext = new AudioContext();
    this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
    // 4096 缓冲在移动端足够稳定
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
    this.processor.onaudioprocess = (event) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const input = event.inputBuffer.getChannelData(0);
      const down = downsampleBuffer(input, this.audioContext!.sampleRate, 16000);
      const pcm = floatTo16BitPCM(down);
      this.ws.send(pcm.buffer);
    };

    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    this.handlers.onStatus?.("listening");
  }

  async stop(): Promise<void> {
    this.closed = true;
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "end" }));
      }
    } catch {
      // ignore
    }

    this.processor?.disconnect();
    this.source?.disconnect();
    this.processor = null;
    this.source = null;

    if (this.audioContext) {
      await this.audioContext.close().catch(() => undefined);
      this.audioContext = null;
    }

    this.mediaStream?.getTracks().forEach((track) => track.stop());
    this.mediaStream = null;

    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        // ignore
      }
      this.ws = null;
    }
    this.handlers.onStatus?.("idle");
  }
}
