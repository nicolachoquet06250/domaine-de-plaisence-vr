/** Pointer ownership and radial dead zone shared by the touchscreen adapter/tests. */
export class TouchInputState {
  movePointer: number | null = null;
  lookPointer: number | null = null;
  x = 0;
  y = 0;
  lookX = 0;
  lookY = 0;
  beginMove(id: number): boolean {
    if (this.movePointer !== null || id === this.lookPointer) return false;
    this.movePointer = id;
    return true;
  }
  move(id: number, dx: number, dy: number, radius: number): boolean {
    if (id !== this.movePointer) return false;
    const length = Math.hypot(dx, dy);
    const magnitude = Math.max(0, (Math.min(length / radius, 1) - .12) / .88);
    this.x = length ? dx / length * magnitude : 0;
    this.y = length ? dy / length * magnitude : 0;
    return true;
  }
  beginLook(id: number, x: number, y: number): boolean {
    if (this.lookPointer !== null || id === this.movePointer) return false;
    this.lookPointer = id; this.lookX = x; this.lookY = y;
    return true;
  }
  end(id: number): void {
    if (id === this.movePointer) { this.movePointer = null; this.x = this.y = 0; }
    if (id === this.lookPointer) this.lookPointer = null;
  }
  reset(): void { this.movePointer = this.lookPointer = null; this.x = this.y = 0; }
}

/** Decorate the SDK's shared public provider, preserving keyboard, gamepad and XR. */
export function attachTouchAxes<T extends { x: number; y: number }>(
  provider: { getMoveAxis(out: T): T }, state: TouchInputState,
  enabled: () => boolean, blocked: () => boolean,
): () => void {
  const original = provider.getMoveAxis;
  const combined = (out: T): T => {
    original.call(provider, out);
    if (!enabled()) return out;
    if (blocked()) { out.x = out.y = 0; return out; }
    out.x += state.x; out.y += state.y;
    const length = Math.hypot(out.x, out.y);
    if (length > 1) { out.x /= length; out.y /= length; }
    return out;
  };
  provider.getMoveAxis = combined;
  return () => { if (provider.getMoveAxis === combined) provider.getMoveAxis = original; };
}
