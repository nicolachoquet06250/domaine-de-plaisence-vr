import { Bone, Quaternion, Vector3, type Object3D } from '@iwsdk/core';

export type HandTarget = { position: Vector3; quaternion: Quaternion; tracked: boolean };
export type ArmLimits = { elbowMin: number; elbowMax: number; shoulderMax: number; wristSwing: number; wristTwist: number; forearmTwist: number };
const defaults: ArmLimits = { elbowMin: 5, elbowMax: 145, shoulderMax: 155, wristSwing: 70, wristTwist: 80, forearmTwist: 90 };
const radians = Math.PI / 180;

/** Reusable analytic two-bone solver. All targets are world-space grip poses. */
export class CourtArmIK {
  readonly wristPosition = new Vector3();
  readonly targetPosition = new Vector3();
  readonly gripPosition = new Vector3();
  error = 0;
  elbowFlex = 0;
  shoulderSwing = 0;
  wristSwing = 0;
  wristTwist = 0;
  forearmTwist = 0;
  private readonly shoulder = new Vector3();
  private readonly elbow = new Vector3();
  private readonly wrist = new Vector3();
  private readonly direction = new Vector3();
  private readonly pole = new Vector3();
  private readonly restDirection = new Vector3();
  private readonly desiredElbow = new Vector3();
  private readonly desiredWrist = new Vector3();
  private readonly current = new Vector3();
  private readonly desired = new Vector3();
  private readonly axis = new Vector3(0, 1, 0);
  private readonly worldQ = new Quaternion();
  private readonly parentQ = new Quaternion();
  private readonly deltaQ = new Quaternion();
  private readonly desiredQ = new Quaternion();
  private readonly twistQ = new Quaternion();
  private readonly swingQ = new Quaternion();
  private readonly identity = new Quaternion();
  private readonly gripOffset = new Quaternion();
  private readonly wristToGrip = new Vector3();
  private readonly gripInHand = new Vector3();
  private readonly targetWrist = new Vector3();
  private readonly modelScale = new Vector3();
  private readonly forearmAxis: Vector3;
  private readonly upperRest: Quaternion;
  private readonly forearmRest: Quaternion;
  private readonly handRest: Quaternion;
  private readonly localRestDirection: Vector3;
  readonly limits: ArmLimits;

  constructor(readonly root: Object3D, readonly upper: Bone, readonly forearm: Bone, readonly hand: Bone, readonly side: 1 | -1, limits: Partial<ArmLimits> = {}) {
    this.limits = { ...defaults, ...limits };
    this.upperRest = upper.quaternion.clone();
    this.forearmRest = forearm.quaternion.clone();
    this.handRest = hand.quaternion.clone();
    this.localRestDirection = forearm.position.clone().normalize().applyQuaternion(this.upperRest);
    this.forearmAxis = hand.position.clone().normalize();
    root.updateWorldMatrix(true, true);
    // Rest anatomy is authored in model space: fingers -Y, thumbs +Z, palms medial.
    // Calibrate the actual Blender bind frame instead of assuming a bone roll.
    // WebXR grip -Z runs toward the thumb along the held handle (not the ray).
    // Blender exports the anatomical grip frame and its palm-centred origin.
    root.getWorldQuaternion(this.parentQ).invert();
    hand.getWorldQuaternion(this.worldQ).premultiply(this.parentQ);
    const grip = hand.userData.xrGrip;
    this.gripOffset.fromArray(grip?.modelToGripQuaternion ?? [0, 1, 0, 0]);
    this.wristToGrip.fromArray(grip?.wristToGripModel ?? [0, 0, 0]);
    this.gripInHand.copy(this.wristToGrip).applyQuaternion(this.deltaQ.copy(this.worldQ).invert());
    this.wristToGrip.applyQuaternion(this.gripOffset);
    this.gripOffset.multiply(this.worldQ);
  }

  private pointBone(bone: Bone, from: Vector3, oldEnd: Vector3, newEnd: Vector3): void {
    this.current.subVectors(oldEnd, from).normalize();
    this.desired.subVectors(newEnd, from).normalize();
    bone.getWorldQuaternion(this.worldQ);
    this.deltaQ.setFromUnitVectors(this.current, this.desired);
    this.worldQ.premultiply(this.deltaQ);
    bone.parent!.getWorldQuaternion(this.parentQ).invert();
    bone.quaternion.copy(this.parentQ).multiply(this.worldQ);
    bone.updateWorldMatrix(false, true);
  }

  solve(target: HandTarget): void {
    if (!target.tracked) { this.error = 0; return; }
    // Tracked arms replace their animation. A stable bind baseline prevents roll
    // from accumulating across repeated solves when an animation does not key it.
    this.upper.quaternion.copy(this.upperRest);
    this.forearm.quaternion.copy(this.forearmRest);
    this.root.updateWorldMatrix(true, true);
    this.upper.getWorldPosition(this.shoulder);
    this.forearm.getWorldPosition(this.elbow);
    this.hand.getWorldPosition(this.wrist);
    const a = this.shoulder.distanceTo(this.elbow), b = this.elbow.distanceTo(this.wrist);
    if (a < 1e-5 || b < 1e-5) return;
    this.targetPosition.copy(target.position);
    this.root.getWorldScale(this.modelScale);
    this.targetWrist.copy(this.wristToGrip).multiply(this.modelScale).applyQuaternion(target.quaternion);
    this.targetWrist.subVectors(target.position, this.targetWrist);
    this.direction.subVectors(this.targetWrist, this.shoulder);
    const requestedDistance = this.direction.length();
    this.upper.parent!.getWorldQuaternion(this.parentQ);
    this.restDirection.copy(this.localRestDirection).applyQuaternion(this.parentQ).normalize();
    if (requestedDistance < 1e-6) this.direction.copy(this.restDirection);
    else this.direction.multiplyScalar(1 / requestedDistance);
    const angle = this.direction.angleTo(this.restDirection), maxShoulder = this.limits.shoulderMax * radians;
    if (angle > maxShoulder) {
      this.deltaQ.setFromUnitVectors(this.restDirection, this.direction);
      this.deltaQ.slerp(this.identity, 1 - maxShoulder / angle);
      this.direction.copy(this.restDirection).applyQuaternion(this.deltaQ);
    }
    const minDistance = Math.sqrt(a * a + b * b + 2 * a * b * Math.cos(this.limits.elbowMax * radians));
    const maxDistance = Math.sqrt(a * a + b * b + 2 * a * b * Math.cos(this.limits.elbowMin * radians));
    const distance = Math.max(minDistance, Math.min(maxDistance, requestedDistance));
    this.desiredWrist.copy(this.shoulder).addScaledVector(this.direction, distance);
    this.root.getWorldQuaternion(this.worldQ);
    this.pole.set(this.side * .35, -1, -.15).applyQuaternion(this.worldQ);
    this.pole.addScaledVector(this.direction, -this.pole.dot(this.direction));
    if (this.pole.lengthSq() < 1e-6) {
      this.pole.set(0, 0, 1).applyQuaternion(this.worldQ);
      this.pole.addScaledVector(this.direction, -this.pole.dot(this.direction));
    }
    this.pole.normalize();
    const along = (a * a - b * b + distance * distance) / (2 * distance);
    const height = Math.sqrt(Math.max(0, a * a - along * along));
    this.desiredElbow.copy(this.shoulder).addScaledVector(this.direction, along).addScaledVector(this.pole, height);
    // Limit the upper arm itself as well as the shoulder-to-grip ray. Folding can otherwise
    // place the elbow outside the shoulder cone even when the wrist is inside it.
    this.current.subVectors(this.desiredElbow, this.shoulder).normalize();
    const upperAngle = this.current.angleTo(this.restDirection);
    if (upperAngle > maxShoulder) {
      this.deltaQ.setFromUnitVectors(this.restDirection, this.current).slerp(this.identity, 1 - maxShoulder / upperAngle);
      this.current.copy(this.restDirection).applyQuaternion(this.deltaQ);
      this.desiredElbow.copy(this.shoulder).addScaledVector(this.current, a);
    }
    this.shoulderSwing = Math.min(upperAngle, maxShoulder) / radians;
    this.desired.subVectors(this.desiredWrist, this.desiredElbow).normalize();
    const requestedFlex = this.current.angleTo(this.desired);
    const flex = Math.max(this.limits.elbowMin * radians, Math.min(this.limits.elbowMax * radians, requestedFlex));
    if (Math.abs(flex - requestedFlex) > 1e-8) {
      // A tiny deterministic bend also handles exactly collinear singularities.
      if (requestedFlex < 1e-6) {
        this.deltaQ.setFromUnitVectors(this.current, this.pole).slerp(this.identity, 1 - flex / (Math.PI / 2));
      } else this.deltaQ.setFromUnitVectors(this.current, this.desired).slerp(this.identity, 1 - flex / requestedFlex);
      this.desired.copy(this.current).applyQuaternion(this.deltaQ);
    }
    this.desiredWrist.copy(this.desiredElbow).addScaledVector(this.desired, b);
    this.pointBone(this.upper, this.shoulder, this.elbow, this.desiredElbow);
    this.forearm.getWorldPosition(this.elbow);
    this.hand.getWorldPosition(this.wrist);
    this.pointBone(this.forearm, this.elbow, this.wrist, this.desiredWrist);
    // Pronation/supination belongs primarily to the forearm, not the wrist.
    this.desiredQ.copy(target.quaternion).multiply(this.gripOffset);
    this.forearm.getWorldQuaternion(this.parentQ).invert();
    this.deltaQ.copy(this.parentQ).multiply(this.desiredQ).multiply(this.twistQ.copy(this.handRest).invert()).normalize();
    if (this.deltaQ.w < 0) this.deltaQ.set(-this.deltaQ.x, -this.deltaQ.y, -this.deltaQ.z, -this.deltaQ.w);
    const projectedTwist = this.deltaQ.x * this.forearmAxis.x + this.deltaQ.y * this.forearmAxis.y + this.deltaQ.z * this.forearmAxis.z;
    const requestedRoll = 2 * Math.atan2(projectedTwist, this.deltaQ.w);
    const rollMax = this.limits.forearmTwist * radians;
    const roll = Math.max(-rollMax, Math.min(rollMax, requestedRoll));
    this.forearm.quaternion.multiply(this.twistQ.setFromAxisAngle(this.forearmAxis, roll));
    this.forearmTwist = roll / radians;
    this.forearm.updateWorldMatrix(false, true);
    // Clamp the remaining wrist swing/twist in its calibrated local bind frame.
    this.forearm.getWorldQuaternion(this.parentQ).invert();
    this.desiredQ.premultiply(this.parentQ);
    this.deltaQ.copy(this.handRest).invert().multiply(this.desiredQ).normalize();
    if (this.deltaQ.w < 0) this.deltaQ.set(-this.deltaQ.x, -this.deltaQ.y, -this.deltaQ.z, -this.deltaQ.w);
    this.twistQ.set(0, this.deltaQ.y, 0, this.deltaQ.w);
    if (this.twistQ.lengthSq() < 1e-8) this.twistQ.identity(); else this.twistQ.normalize();
    let twist = 2 * Math.atan2(this.twistQ.y, this.twistQ.w);
    this.swingQ.copy(this.twistQ).invert().premultiply(this.deltaQ);
    const swing = 2 * Math.acos(Math.min(1, Math.abs(this.swingQ.w)));
    const swingMax = this.limits.wristSwing * radians;
    if (swing > swingMax) this.swingQ.slerp(this.identity, 1 - swingMax / swing);
    twist = Math.max(-this.limits.wristTwist * radians, Math.min(this.limits.wristTwist * radians, twist));
    this.twistQ.setFromAxisAngle(this.axis, twist);
    this.hand.quaternion.copy(this.handRest).multiply(this.swingQ).multiply(this.twistQ);
    this.hand.updateWorldMatrix(false, true);
    this.hand.getWorldPosition(this.wristPosition);
    this.gripPosition.copy(this.gripInHand); this.hand.localToWorld(this.gripPosition);
    this.error = this.gripPosition.distanceTo(target.position);
    this.elbowFlex = flex / radians;
    this.wristSwing = Math.min(swing, swingMax) / radians;
    this.wristTwist = twist / radians;
  }
}

export function createCourtArmIK(model: Object3D): { left?: CourtArmIK; right?: CourtArmIK } {
  const result: { left?: CourtArmIK; right?: CourtArmIK } = {};
  let limits: Partial<ArmLimits> = {};
  model.traverse(object => { if (object.userData.armIK) limits = object.userData.armIK; });
  model.updateWorldMatrix(true, true);
  const position = new Vector3();
  model.traverse(object => {
    // GLTFLoader strips periods for PropertyBinding: Blender's UpperArm.L becomes UpperArmL.
    if (!(object as Bone).isBone || !/^UpperArm[._]?[LR](?:[._]\d+)?$/.test(object.name)) return;
    const forearm = object.children.find(child => (child as Bone).isBone && /^Forearm[._]?[LR](?:[._]\d+)?$/.test(child.name));
    const hand = forearm?.children.find(child => (child as Bone).isBone && /^Hand[._]?[LR](?:[._]\d+)?$/.test(child.name));
    if (!forearm || !hand) return;
    object.getWorldPosition(position); model.worldToLocal(position);
    const side = position.x > 0 ? 1 : -1;
    result[side === 1 ? 'left' : 'right'] = new CourtArmIK(model, object as Bone, forearm as Bone, hand as Bone, side, limits);
  });
  return result;
}
