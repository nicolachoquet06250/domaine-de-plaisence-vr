import { createComponent, Types } from '@iwsdk/core';
export const ArrivalBoundary=createComponent('ArrivalBoundary',{
  radius:{type:Types.Float32,default:8.1},
  spawn:{type:Types.Vec3,default:[0,0,2]},
  recoveries:{type:Types.Int32,default:0},
});
