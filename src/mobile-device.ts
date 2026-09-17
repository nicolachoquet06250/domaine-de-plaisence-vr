type DeviceNavigator = Pick<Navigator, 'userAgent' | 'platform' | 'maxTouchPoints'>;

/** Coarse input alone also matches headsets and touchscreen computers. */
export function isMobileTouchDevice(device: DeviceNavigator, coarsePointer: boolean): boolean {
  const ua = device.userAgent;
  // Headset browsers commonly include Android and Mobile in their user agent.
  if (/Oculus|Quest|Pico|Wolvic|Vive|VRBrowser|VR Chrome|VisionOS|Vision Pro/i.test(ua)) return false;
  if (/Windows|CrOS/i.test(ua)) return false;
  const phoneOrTablet = /Android|iPhone|iPad|iPod/i.test(ua);
  // iPadOS can request desktop pages and identify itself as a Mac.
  const desktopIPad = /Macintosh|MacIntel/i.test(`${ua} ${device.platform}`) && device.maxTouchPoints > 1;
  return (phoneOrTablet || desktopIPad) && (coarsePointer || device.maxTouchPoints > 0);
}
