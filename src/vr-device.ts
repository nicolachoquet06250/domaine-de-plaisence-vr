type VRDeviceNavigator = Pick<Navigator, 'userAgent' | 'platform'>;

/** Device targeting is separate from WebXR support (also emulated on PCs). */
export function isVRHeadsetBrowser(device: VRDeviceNavigator): boolean {
  // IWSDK emulates a Quest user agent but retains the computer's platform.
  if (/Win|Mac|Linux (?:x86_64|i[3-6]86)|CrOS/i.test(device.platform)) return false;
  return /OculusBrowser|Quest|Pico|Wolvic|Vive|VRBrowser|VR Chrome|VisionOS|Vision Pro|Android XR/i.test(device.userAgent);
}
