import { createSystem, LocomotionEnvironment, LocomotionSystem, Transform, Vector3 } from '@iwsdk/core';
import { StaticCollision } from './collision-components.js';

export class StaticCollisionSystem extends createSystem({
  pending: { required: [StaticCollision, Transform], excluded: [LocomotionEnvironment] },
  registered: { required: [StaticCollision, LocomotionEnvironment] },
}) {
  private spawn = new Vector3();
  private restoreSpawn = true;

  init() {
    const locomotion = this.world.getSystem(LocomotionSystem);
    if (locomotion) this.spawn.fromArray(locomotion.config.initialPlayerPosition.peek());
    this.cleanupFuncs.push(this.world.onAuthoredPlayerPosition((position) => {
      this.spawn.copy(position);
      this.restoreSpawn = true;
    }));
  }

  // Run after TransformSystem (priority 0). Locomotor captures matrixWorld once
  // on qualification; scene loading has not attached every ancestor at that point.
  update() {
    for (const entity of this.queries.pending.entities) {
      const object = entity.object3D;
      if (!object?.parent) continue;
      object.updateWorldMatrix(true, true);
      entity.addComponent(LocomotionEnvironment);
    }
    // GLB decoding can finish after locomotion has started falling. Queue the
    // authored spawn after the worker's environment messages, once per load.
    if (!this.restoreSpawn || this.queries.pending.entities.size > 0 || this.queries.registered.entities.size === 0) return;
    for (const entity of this.queries.registered.entities) {
      if (!entity.getValue(LocomotionEnvironment, '_initialized')) return;
    }
    const locomotion = this.world.getSystem(LocomotionSystem);
    if (locomotion) {
      locomotion.setPlayerPosition(this.spawn);
      this.restoreSpawn = false;
    }
  }
}
