/** Stable public identity values; asset paths are never accepted from the network. */
export function cleanAvatar(value) {
  return value === 'male' || value === 'female' ? value : null;
}
export function visitorAvatar(value) { return cleanAvatar(value) ?? 'male'; }
