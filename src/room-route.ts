export const ROOM_ID = /^[a-f0-9]{32}$/;
export function readRoomId(url:URL):string | null {
  const value = url.searchParams.get('roomId') ?? url.searchParams.get('room');
  return value && ROOM_ID.test(value) ? value : null;
}
export function newRoomId():string {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, '0')).join('');
}
export function roomUrl(current:URL, room:string | null, base:string):URL {
  const url = new URL(current);
  url.searchParams.delete('room'); url.searchParams.delete('roomId');
  if (room) url.searchParams.set('roomId', room);
  else { url.pathname = base; url.hash = ''; }
  return url;
}
export function initialRoom(url:URL):string | null {
  return readRoomId(url);
}
