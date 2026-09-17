import { attachRooms } from './rooms.mjs';

export function roomsPlugin() {
  return {
    name: 'plaisance-rooms',
    configureServer(server) {
      if (server.httpServer) attachRooms(server.httpServer);
    },
    configurePreviewServer(server) {
      if (server.httpServer) attachRooms(server.httpServer);
    },
  };
}
