import { CircleGeometry, Mesh, MeshStandardMaterial, PlaneGeometry } from '@iwsdk/core';

const silver = new MeshStandardMaterial({ color: 0xcbd1d3, metalness: 1, roughness: .07 });
export const mirrorRectangle = new Mesh(new PlaneGeometry(1, 1), silver);
export const mirrorOval = new Mesh(new CircleGeometry(1, 64), silver);
mirrorRectangle.name = 'Surface de miroir rectangulaire';
mirrorOval.name = 'Surface de miroir ovale';
