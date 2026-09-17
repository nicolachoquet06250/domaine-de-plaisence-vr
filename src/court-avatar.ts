import { AnimationMixer, AssetManager, LoopRepeat, Quaternion, Vector3, type AnimationAction, type Bone, type Object3D, type SkinnedMesh } from '@iwsdk/core';
import type { AvatarGender } from '../server/avatar.mjs';
import { createCourtArmIK, type CourtArmIK, type HandTarget } from './court-avatar-ik.js';
import { REFLECTION_ONLY_LAYER } from './planar-reflection.js';
import { VISEME_NAMES } from './speech-visemes.js';
import { createAvatarHair, type AvatarHair } from './hair-particles.js';

export type AvatarMotion = { velocity: Vector3; left: HandTarget; right: HandTarget };
export type AvatarDiagnostics = { mode: string; leftTracked: boolean; rightTracked: boolean; leftError: number; rightError: number; leftWrist: Vector3; rightWrist: Vector3; leftFlex: number; rightFlex: number };
type AvatarView = 'world' | 'first-person' | 'reflection-only';
type Playback = { cancelled: boolean; view: AvatarView; originalLayers: WeakMap<Object3D, number>; mouths: { influences: number[]; indices: number[] }[]; hair?: AvatarHair[]; model?: Object3D; mixer?: AnimationMixer; idle?: AnimationAction; walking?: AnimationAction; strafeLeft?: AnimationAction; strafeRight?: AnimationAction; blend: number; leftBlend: number; rightBlend: number; left?: CourtArmIK; right?: CourtArmIK; diagnostics: AvatarDiagnostics };
const playback = new WeakMap<Object3D, Playback>();
const localVelocity = new Vector3();
const inverseRotation = new Quaternion();

/** +Z faces forwards; anatomical left is +X. Does not rotate the body toward movement. */
export function courtLocomotionMode(x: number, z: number): string {
  if (Math.hypot(x, z) < .06) return 'Idle';
  if (Math.abs(x) > Math.abs(z)) return x > 0 ? 'StrafeLeft' : 'StrafeRight';
  return 'Walking';
}
export function courtAvatarDiagnostics(root: Object3D): AvatarDiagnostics | undefined { return playback.get(root)?.diagnostics; }
export function courtHairDiagnostics(root: Object3D): readonly AvatarHair[] | undefined { return playback.get(root)?.hair; }

/** Morph weights belong to each avatar clone and combine with its existing skeletal clips/IK. */
export function animateCourtMouth(root: Object3D, weights?: Float32Array): void {
  const state = playback.get(root); if (!state) return;
  for (const mouth of state.mouths) for (let i = 0; i < mouth.indices.length; i++) {
    const index = mouth.indices[i];
    if (index >= 0) mouth.influences[index] = Math.max(0, Math.min(1, weights?.[i] ?? 0));
  }
}

function applyAvatarView(state: Playback): void {
  state.model?.traverse(object => {
    const hideHead = state.view === 'first-person' && !(object as Bone).isBone &&
      (object.userData.firstPersonHidden || /(?:^|[ _-])(Head|Hair|Neck)(?:[ _-]|$)/i.test(object.name));
    object.layers.mask = state.view === 'reflection-only' || hideHead
      ? 1 << REFLECTION_ONLY_LAYER : state.originalLayers.get(object)!;
  });
}

/** Keep the local model alive for mirrors; only its direct-camera layers change. */
export function setCourtAvatarView(root: Object3D, view: AvatarView): void {
  const state = playback.get(root);
  if (!state || state.view === view) return;
  state.view = view;
  applyAvatarView(state);
}

/** AssetManager clones the complete bone hierarchy with SkeletonUtils internally. */
export async function setCourtAvatar(root: Object3D, gender: AvatarGender, firstPerson = false): Promise<void> {
  releaseCourtAvatar(root);
  const state: Playback = { cancelled: false, view: firstPerson ? 'first-person' : 'world', originalLayers: new WeakMap(), mouths: [], blend: 0, leftBlend: 0, rightBlend: 0,
    diagnostics: { mode: 'Idle', leftTracked: false, rightTracked: false, leftError: 0, rightError: 0, leftWrist: new Vector3(), rightWrist: new Vector3(), leftFlex: 0, rightFlex: 0 } };
  playback.set(root, state);
  const id = gender === 'female' ? 'courtFemale' : 'courtMale';
  try { await AssetManager.loadGLTFById(id); }
  catch (error) { if (state.cancelled) return; throw error; }
  if (state.cancelled) return;
  const gltf = AssetManager.getGLTF(id);
  if (!gltf) throw new Error(`Avatar unavailable: ${id}`);
  const idle = gltf.animations.find(clip => clip.name === 'Idle');
  const walking = gltf.animations.find(clip => clip.name === 'Walking');
  const strafeLeft = gltf.animations.find(clip => clip.name === 'StrafeLeft');
  const strafeRight = gltf.animations.find(clip => clip.name === 'StrafeRight');
  if (!idle || !walking || !strafeLeft || !strafeRight) throw new Error(`Avatar ${id} requires Idle, Walking, StrafeLeft and StrafeRight clips`);
  state.model = gltf.scene;
  state.model.name = `court-avatar-${gender}`;
  state.hair = createAvatarHair(state.model);
  state.model.traverse(object => {
    state.originalLayers.set(object, object.layers.mask);
    const mesh = object as SkinnedMesh;
    if (mesh.morphTargetDictionary && mesh.morphTargetInfluences) {
      const indices = VISEME_NAMES.map(name => mesh.morphTargetDictionary![name] ?? -1);
      if (indices.some(index => index >= 0)) state.mouths.push({ influences: mesh.morphTargetInfluences, indices });
    }
    if ((object as SkinnedMesh).isSkinnedMesh) object.frustumCulled = false;
  });
  applyAvatarView(state);
  root.add(state.model);
  const arms = createCourtArmIK(state.model); state.left = arms.left; state.right = arms.right;
  state.mixer = new AnimationMixer(state.model);
  state.idle = state.mixer.clipAction(idle).setLoop(LoopRepeat, Infinity).play();
  state.walking = state.mixer.clipAction(walking).setLoop(LoopRepeat, Infinity).setEffectiveWeight(0).play();
  state.strafeLeft = state.mixer.clipAction(strafeLeft).setLoop(LoopRepeat, Infinity).setEffectiveWeight(0).play();
  state.strafeRight = state.mixer.clipAction(strafeRight).setLoop(LoopRepeat, Infinity).setEffectiveWeight(0).play();
}

/** Continuous weights prevent rapid 10 Hz pose arrivals from restarting animation clips. */
export function animateCourtAvatar(root: Object3D, delta: number, speed = 0, motion?: AvatarMotion): void {
  const state = playback.get(root);
  if (!state?.mixer || !state.idle || !state.walking) return;
  let mode = speed > .06 ? 'Walking' : 'Idle';
  if (motion) {
    root.getWorldQuaternion(inverseRotation).invert();
    localVelocity.copy(motion.velocity).applyQuaternion(inverseRotation);
    speed = Math.hypot(localVelocity.x, localVelocity.z);
    mode = courtLocomotionMode(localVelocity.x, localVelocity.z);
  }
  const target = Math.min(1, Math.max(0, (speed - .06) / .55));
  const alpha = 1 - Math.exp(-8 * delta);
  state.blend += (target - state.blend) * alpha;
  state.leftBlend += ((mode === 'StrafeLeft' ? 1 : 0) - state.leftBlend) * alpha;
  state.rightBlend += ((mode === 'StrafeRight' ? 1 : 0) - state.rightBlend) * alpha;
  state.idle.setEffectiveWeight(1 - state.blend);
  const rate = Math.min(1.7, Math.max(.55, speed / 1.35));
  state.walking.setEffectiveWeight(state.blend * (1 - state.leftBlend - state.rightBlend)).setEffectiveTimeScale(rate * (motion && localVelocity.z < -.06 ? -1 : 1));
  state.strafeLeft?.setEffectiveWeight(state.blend * state.leftBlend).setEffectiveTimeScale(rate);
  state.strafeRight?.setEffectiveWeight(state.blend * state.rightBlend).setEffectiveTimeScale(rate);
  state.mixer.update(Math.min(delta, .1));
  state.diagnostics.mode = mode;
  state.diagnostics.leftTracked = !!(motion?.left.tracked && state.left);
  state.diagnostics.rightTracked = !!(motion?.right.tracked && state.right);
  if (motion) {
    state.left?.solve(motion.left); state.right?.solve(motion.right);
    if (state.left) { state.diagnostics.leftError = state.left.error; state.diagnostics.leftFlex = state.left.elbowFlex; state.diagnostics.leftWrist.copy(state.left.wristPosition); }
    if (state.right) { state.diagnostics.rightError = state.right.error; state.diagnostics.rightFlex = state.right.elbowFlex; state.diagnostics.rightWrist.copy(state.right.wristPosition); }
  }
  if (state.hair) for (const hair of state.hair) hair.update(delta);
}

export function releaseCourtAvatar(root: Object3D): void {
  const state = playback.get(root);
  if (!state) return;
  state.cancelled = true;
  state.mixer?.stopAllAction();
  if (state.hair) for (const hair of state.hair) hair.dispose();
  if (state.model) {
    state.mixer?.uncacheRoot(state.model);
    state.model.removeFromParent();
    // Geometry/materials belong to AssetManager. Only each cloned skeleton is private.
    state.model.traverse(object => { if ((object as SkinnedMesh).isSkinnedMesh) (object as SkinnedMesh).skeleton.dispose(); });
  }
  playback.delete(root);
}
