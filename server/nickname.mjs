/** Shared client/server rules; a nickname is plain text, never markup. */
export function cleanNickname(value) {
  if (typeof value !== 'string') return '';
  return Array.from(value.slice(0,256).normalize('NFKC')
    .replace(/[\p{Cc}\p{Cf}]/gu, '').replace(/\s+/gu, ' ').trim()).slice(0,24).join('');
}
export function visitorNickname(value, id) {
  return cleanNickname(value) || `Visiteur-${id.slice(0,4)}`;
}
