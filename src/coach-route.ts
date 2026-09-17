import { CatmullRomCurve3, Vector3 } from '@iwsdk/core';

export const WICKET_X = 7.555815805552804;
export const ARRIVAL_DROP = [5.4, 0, 0] as const;
export const CASTLE_DROP = [100, .12, -70] as const;
export const CASTLE_STOP = [100, .048, -57.5] as const;
export const COACH_SEAT = [-.60, 2.08, 0] as const;
export const WALK_SPEED = 1.0833333333;
export const CRUISE_SPEED = 2.0;

export function roadHeight(x:number,z:number):number {
  return .048 + .18 * Math.sin(Math.PI * Math.min(1, Math.max(0,(Math.hypot(x,z)-8)/16))) ** 2;
}

/** Baked arc-length lookup. Sampling allocates no objects during a frame. */
export class CoachRoute {
  readonly length:number;
  readonly points:Float64Array;
  readonly count=2048;
  private tangentPoint=new Vector3();
  private previousPoint=new Vector3();
  constructor(curve:CatmullRomCurve3) {
    curve.arcLengthDivisions=4096;curve.updateArcLengths();this.length=curve.getLength();
    this.points=new Float64Array((this.count+1)*3);
    const p=new Vector3();
    for(let i=0;i<=this.count;i++){
      curve.getPointAt(i/this.count,p);this.points[i*3]=p.x;
      this.points[i*3+1]=roadHeight(p.x,p.z);this.points[i*3+2]=p.z;
    }
  }
  point(distance:number,out:Vector3):Vector3 {
    const t=Math.max(0,Math.min(1,distance/this.length))*this.count;
    const i=Math.min(this.count-1,Math.floor(t)),alpha=t-i,j=i*3;
    return out.set(this.points[j]+(this.points[j+3]-this.points[j])*alpha,
      this.points[j+1]+(this.points[j+4]-this.points[j+1])*alpha,
      this.points[j+2]+(this.points[j+5]-this.points[j+2])*alpha);
  }
  sample(distance:number,out:Vector3):number {
    this.point(distance,out);
    this.point(Math.min(this.length,distance+.5),this.tangentPoint);
    this.point(Math.max(0,distance-.5),this.previousPoint);
    this.tangentPoint.sub(this.previousPoint);
    return -Math.atan2(this.tangentPoint.z,this.tangentPoint.x);
  }
}

export function createCoachRoutes():{outbound:CoachRoute;inbound:CoachRoute} {
  // Exact Catmull-Rom construction used by the Blender gravel generator.
  const controls=[[8.025,0],[13,0],[20,-5],[29,-2],[43,-12],[53,-26],[70,-23],[88,-35],[100,-49],[100,-68]];
  const points:Vector3[]=[];
  for(let k=0;k<controls.length-1;k++)for(let j=0;j<24;j++){
    const t=j/24,p0=controls[Math.max(0,k-1)],p1=controls[k],p2=controls[k+1],p3=controls[Math.min(controls.length-1,k+2)];
    const value=(axis:number)=>.5*(2*p1[axis]+(-p0[axis]+p2[axis])*t+(2*p0[axis]-5*p1[axis]+4*p2[axis]-p3[axis])*t*t+(-p0[axis]+3*p1[axis]-3*p2[axis]+p3[axis])*t*t*t);
    points.push(new Vector3(value(0),0,value(1)));
  }
  points.push(new Vector3(100,0,-68));
  let arc=0,start=0;
  for(let i=1;i<points.length;i++){arc+=points[i].distanceTo(points[i-1]);if(arc>=5-(8.025-WICKET_X)){start=i;break;}}
  const visible=points.slice(start).filter(p=>p.z>=CASTLE_STOP[2]);
  visible[0].set(12.510428931294015,0,.1713448801171473);
  // Centre the final approach gradually so the parked coach faces the gate.
  for(const p of visible){
    const t=Math.max(0,Math.min(1,(-p.z-49)/6));
    p.x+=(100-p.x)*t*t*(3-2*t);
  }
  visible.push(new Vector3(CASTLE_STOP[0],0,CASTLE_STOP[2]));
  const outbound=new CoachRoute(new CatmullRomCurve3(visible,false,'centripetal'));
  // Broad 9 m diameter U-turn in the forecourt, tangent-continuous at the start.
  const back:Vector3[]=[];
  for(let i=0;i<=24;i++){const a=i*Math.PI/24;back.push(new Vector3(104.5-4.5*Math.cos(a),0,-57.5-4.5*Math.sin(a)));}
  // Cubic connector from the turn exit to the reversed main ribbon.
  for(let i=1;i<=20;i++){
    const t=i/20,u=1-t;
    back.push(new Vector3(u*u*u*109+3*u*u*t*109+3*u*t*t*101+t*t*t*100,0,u*u*u*-57.5+3*u*u*t*-51+3*u*t*t*-55+t*t*t*-49));
  }
  for(const p of [...visible].reverse())if(p.z>-49.0)back.push(p.clone());
  return {outbound,inbound:new CoachRoute(new CatmullRomCurve3(back,false,'centripetal'))};
}
