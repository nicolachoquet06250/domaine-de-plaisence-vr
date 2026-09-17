/** HeadAudio's Oculus viseme order. One shape covers several visually identical sounds. */
export const VISEME_NAMES = ['viseme_aa','viseme_E','viseme_I','viseme_O','viseme_U','viseme_PP','viseme_SS','viseme_TH','viseme_DD','viseme_FF','viseme_kk','viseme_nn','viseme_RR','viseme_CH','viseme_sil'] as const;
type Prototype = { phoneme: string; group: number; viseme: number; mu: Float32Array; sigmaInvLower: Float32Array };
const contexts = new WeakMap<AudioContext, Promise<Prototype[]>>();
let model: Promise<Prototype[]> | undefined;

/** Decode the pinned HeadAudio MFCC/Gaussian model, without a speech transcription service. */
export function decodeVisemeModel(buffer: ArrayBuffer): Prototype[] {
  if (!buffer.byteLength || buffer.byteLength % 368) throw new Error('Invalid viseme model size');
  const result: Prototype[] = [];
  for (let offset = 0; offset < buffer.byteLength; offset += 368) {
    const header = new DataView(buffer, offset, 8), packed = header.getUint32(0);
    const first = packed >>> 16, second = packed & 65535, viseme = header.getUint8(7);
    const mu = new Float32Array(buffer, offset + 8, 12), sigmaInvLower = new Float32Array(buffer, offset + 56, 78);
    if (viseme >= 15 || !mu.every(Number.isFinite) || !sigmaInvLower.every(Number.isFinite)) throw new Error('Invalid viseme prototype');
    result.push({ phoneme: second ? String.fromCodePoint(first, second) : String.fromCodePoint(first), group: header.getUint8(5), viseme, mu, sigmaInvLower });
  }
  return result;
}

function prepare(context: AudioContext): Promise<Prototype[]> {
  const existing = contexts.get(context); if (existing) return existing;
  const base = `${import.meta.env.BASE_URL}vendor/headaudio/`;
  if (!model) model = fetch(`${base}model-en-mixed.bin`).then(r => {
    if (!r.ok) throw new Error(`Viseme model: ${r.status}`); return r.arrayBuffer();
  }).then(decodeVisemeModel).catch(error => { model = undefined; throw error; });
  const promise = Promise.all([context.audioWorklet.addModule(`${base}headworklet.mjs`), model]).then(([, prototypes]) => prototypes);
  contexts.set(context, promise);
  void promise.catch(() => contexts.delete(context));
  return promise;
}

/** One silent analysis branch per live voice; the worklet performs DSP off the render thread. */
export class SpeechVisemes {
  readonly weights = new Float32Array(15);
  readonly ready: Promise<void>;
  status: 'loading' | 'ready' | 'unavailable' | 'disposed' = 'loading';
  private node?: AudioWorkletNode;
  private active = true;
  private disposed = false;
  private detected = 14;
  private receivedAt = -Infinity;

  constructor(private readonly context: AudioContext, private readonly source: AudioNode) {
    this.ready = this.initialize().catch(error => {
      if (this.disposed) return;
      this.status = 'unavailable';
      console.warn('Lip sync unavailable; voice remains connected', error);
    });
  }

  private async initialize(): Promise<void> {
    if (!this.context.audioWorklet || typeof AudioWorkletNode === 'undefined') throw new Error('AudioWorklet unavailable');
    const prototypes = await prepare(this.context);
    if (this.disposed) return;
    const node = new AudioWorkletNode(this.context, 'headworklet', {
      numberOfInputs: 1, numberOfOutputs: 0, outputChannelCount: [],
      channelCount: 1, channelCountMode: 'explicit', channelInterpretation: 'speakers',
      parameterData: { vadMode: 1, vadGateActiveDb: -42, vadGateInactiveDb: -52, silMode: 0 },
    });
    this.node = node;
    node.port.onmessage = event => {
      if (this.disposed || !this.active) return;
      const message = event.data;
      if (message.event === 'viseme' && Number.isInteger(message.viseme) && message.viseme >= 0 && message.viseme < 15) {
        this.detected = message.viseme; this.receivedAt = this.context.currentTime;
      } else if (message.event === 'ended' || message.event === 'end') this.detected = 14;
    };
    node.onprocessorerror = () => { this.status = 'unavailable'; this.detected = 14; this.weights.fill(0); };
    node.port.postMessage({ event: 'model', model: prototypes });
    if (!this.active) node.port.postMessage({ event: 'stop' });
    this.source.connect(node);
    this.status = 'ready';
  }

  sample(delta: number, active = true): Float32Array {
    active = active && !this.disposed && this.context.state === 'running';
    if (active !== this.active) {
      this.active = active; this.detected = 14; this.receivedAt = -Infinity;
      this.node?.port.postMessage({ event: active ? 'start' : 'stop' });
    }
    const target = active && this.context.currentTime - this.receivedAt < .25 ? this.detected : 14;
    const alpha = 1 - Math.exp(-Math.min(.1, Math.max(0, delta)) * 22);
    for (let i = 0; i < 15; i++) this.weights[i] += ((i === target && i !== 14 ? .85 : 0) - this.weights[i]) * alpha;
    return this.weights;
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true; this.status = 'disposed'; this.weights.fill(0);
    if (this.node) {
      this.source.disconnect(this.node);
      this.node.port.postMessage({ event: 'stop' }); this.node.port.onmessage = null;
      this.node.onprocessorerror = null; this.node.disconnect(); this.node.port.close(); this.node = undefined;
    }
  }
}
