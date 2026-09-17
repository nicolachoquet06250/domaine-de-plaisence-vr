/** Three normalized voice bands, sampled only when serializing the 10 Hz pose. */
export function voiceBands(bins: Uint8Array, sampleRate: number, fftSize: number, output: number[]): void {
  for(let band=0;band<3;band++) {
    const low=band===0?80:band===1?400:2000,high=band===0?400:band===1?2000:8000;
    let peak=0;
    for(let i=Math.ceil(low*fftSize/sampleRate);i<Math.min(bins.length,Math.ceil(high*fftSize/sampleRate));i++)peak=Math.max(peak,bins[i]);
    output[band]=Math.round(100*(peak/255)**2)/100;
  }
}

export class VoiceSpectrum {
  readonly bands=[0,0,0];
  private readonly analyser: AnalyserNode;
  private readonly bins=new Uint8Array(512);
  private readonly wave=new Float32Array(1024);
  private lastVoice=-Infinity;
  constructor(private readonly context:AudioContext,private readonly source:AudioNode) {
    this.analyser=context.createAnalyser();this.analyser.fftSize=1024;
    this.analyser.minDecibels=-65;this.analyser.maxDecibels=-15;
    this.analyser.smoothingTimeConstant=.35;
    source.connect(this.analyser);
  }
  sample(active:boolean):number[] {
    if(!active||this.context.state!=='running'){this.bands.fill(0);return this.bands;}
    this.analyser.getFloatTimeDomainData(this.wave);
    let energy=0;for(let i=0;i<this.wave.length;i++)energy+=this.wave[i]*this.wave[i];
    if(Math.sqrt(energy/this.wave.length)>.006)this.lastVoice=this.context.currentTime;
    if(this.context.currentTime-this.lastVoice>.18){this.bands.fill(0);return this.bands;}
    this.analyser.getByteFrequencyData(this.bins);
    voiceBands(this.bins,this.context.sampleRate,this.analyser.fftSize,this.bands);
    return this.bands;
  }
  dispose():void {this.source.disconnect(this.analyser);this.analyser.disconnect();this.bands.fill(0);}
}
