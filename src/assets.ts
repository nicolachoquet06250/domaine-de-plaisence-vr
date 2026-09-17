import { AssetType, defineAssets } from '@iwsdk/core';
import palaceCollision from './scene-assets/palace-collision.scene-asset.js';
import palaceDoorCollision from './scene-assets/palace-door-collision.scene-asset.js';
import { ground, parterre, cypress, bench as benchCollisionProxy, urn, gardenBorder, path } from './scene-assets/garden-collision.scene-asset.js';
import { basin as basinCollisionProxy } from './scene-assets/fountain.scene-asset.js';
import { createStaticCollision } from './scene-assets/static-collision.js';
import arrivalCollisionProxy from './scene-assets/arrival.scene-asset.js';
import { mirrorOval, mirrorRectangle } from './scene-assets/mirrors.scene-asset.js';
import { hearthFire } from './scene-assets/hearth-fire.scene-asset.js';
import arrivalBoundary from './scene-assets/arrival-boundary.scene-asset.js';
import royalEnclosureCollision from './scene-assets/royal-enclosure-collision.scene-asset.js';
import coachPortal from './scene-assets/coach-portal.scene-asset.js';
import portalDirection from './scene-assets/portal-direction.scene-asset.js';
export default defineAssets({
  portalDirection,
  'environment-desk': {url:'https://cdn.jsdelivr.net/npm/@iwsdk/example-assets@0.4.2/assets/environment-desk/environmentDesk.gltf',type:AssetType.GLTF,priority:'lazy'},
  'plant-sansevieria': {url:'https://cdn.jsdelivr.net/npm/@iwsdk/example-assets@0.4.2/assets/plant-sansevieria/plantSansevieria.gltf',type:AssetType.GLTF,priority:'lazy'},
  robot: {url:'https://cdn.jsdelivr.net/npm/@iwsdk/example-assets@0.4.2/assets/robot/robot.gltf',type:AssetType.GLTF,priority:'lazy'},
  'welcome-panel': {url:`${import.meta.env.BASE_URL}ui/welcome.uikitml`,type:AssetType.UIKitML,priority:'lazy'},
  'webxr-banner': {url:`${import.meta.env.BASE_URL}gltf/webxr-banner/banner.gltf`,type:AssetType.GLTF,priority:'lazy'},
  palace: { url: `${import.meta.env.BASE_URL}gltf/castle/palace.glb?v=chimney-walls-20260910`, type: AssetType.GLTF, name: 'Chateau sculpte et dore — Blender', priority: 'lazy' },
  palaceInterior: { url: `${import.meta.env.BASE_URL}gltf/castle/palaceInterior.glb?v=makehuman-busts-20260913-r3`, type: AssetType.GLTF, name: 'Salons et grand escalier — Blender', priority: 'lazy' },
  palaceGlass: { url: `${import.meta.env.BASE_URL}gltf/castle/palaceGlass.glb?v=chimney-walls-20260910`, type: AssetType.GLTF, name: 'Vitrages clairs reflechissants — Blender', priority: 'lazy' },
  palaceDoor: { url: `${import.meta.env.BASE_URL}gltf/castle/palaceDoor.glb`, type: AssetType.GLTF, name: 'Portes sculptees animees — Blender', priority: 'lazy' },
  palaceCollision, palaceDoorCollision,
  mirrorOval, mirrorRectangle,
  hearthFire,
  hearth: { url: `${import.meta.env.BASE_URL}gltf/castle/hearth.glb`, type: AssetType.GLTF, name: 'Buches, braises et grille en fer forge — Blender', priority: 'lazy' },
  bustFrancoisI: { url: `${import.meta.env.BASE_URL}gltf/castle/bustFrancoisI.glb?v=makehuman-busts-20260913-r3`, type: AssetType.GLTF, name: 'Francois Ier — portrait sculpte', priority: 'lazy' },
  bustLouisXIV: { url: `${import.meta.env.BASE_URL}gltf/castle/bustLouisXIV.glb?v=makehuman-busts-20260913-r3`, type: AssetType.GLTF, name: 'Louis XIV — portrait sculpte', priority: 'lazy' },
  bustCatherineMedici: { url: `${import.meta.env.BASE_URL}gltf/castle/bustCatherineMedici.glb?v=makehuman-busts-20260913-r3`, type: AssetType.GLTF, name: 'Catherine de Médicis — MakeHuman, d’après Clouet', priority: 'lazy' },
  bustAnneFrance: { url: `${import.meta.env.BASE_URL}gltf/castle/bustAnneFrance.glb?v=makehuman-busts-20260913-r3`, type: AssetType.GLTF, name: 'Anne de France — MakeHuman, d’après Jean Hey', priority: 'lazy' },
  courtMale: { url: `${import.meta.env.BASE_URL}gltf/avatars/courtMale.glb?v=moustache-20260913-r1`, type: AssetType.GLTF, name: 'Courtisan Renaissance — avatar anime', priority: 'lazy' },
  courtFemale: { url: `${import.meta.env.BASE_URL}gltf/avatars/courtFemale.glb?v=francois-20260912-r2`, type: AssetType.GLTF, name: 'Dame de cour Renaissance — avatar anime', priority: 'lazy' },
  ground: { url: `${import.meta.env.BASE_URL}gltf/royal-enclosure/estateLawnReliefGate.glb`, type: AssetType.GLTF, name: 'Pelouse en relief et brins — Blender', priority: 'lazy' },
  coachEstateLawn: { url: `${import.meta.env.BASE_URL}gltf/arrival-coach/estateLawnCoach.glb`, type: AssetType.GLTF, name: 'Pelouse avec aire de retournement', priority: 'lazy' },
  parterre: { url: `${import.meta.env.BASE_URL}gltf/garden/parterre.glb`, type: AssetType.GLTF, name: 'Buis, rosiers et topiaires — Blender', priority: 'lazy' },
  cypress: { url: `${import.meta.env.BASE_URL}gltf/garden/cypress.glb`, type: AssetType.GLTF, name: 'Cypres a feuillage detaille — Blender', priority: 'lazy' },
  urn: { url: `${import.meta.env.BASE_URL}gltf/garden/urn.glb`, type: AssetType.GLTF, name: 'Vase Medicis fleuri — Blender', priority: 'lazy' },
  gardenBorder: { url: `${import.meta.env.BASE_URL}gltf/garden/gardenBorder.glb`, type: AssetType.GLTF, name: 'Muret de pierre appareillee — Blender', priority: 'lazy' },
  path: { url: `${import.meta.env.BASE_URL}gltf/garden/path.glb`, type: AssetType.GLTF, name: 'Allee de gravier — Blender', priority: 'lazy' },
  pathLong: { url: `${import.meta.env.BASE_URL}gltf/garden/pathLong.glb`, type: AssetType.GLTF, name: 'Gravier — allee axiale', priority: 'lazy' },
  pathCross: { url: `${import.meta.env.BASE_URL}gltf/garden/pathCross.glb`, type: AssetType.GLTF, name: 'Gravier — allee transversale', priority: 'lazy' },
  pathTerrace: { url: `${import.meta.env.BASE_URL}gltf/garden/pathTerrace.glb`, type: AssetType.GLTF, name: 'Gravier — terrasse et entree', priority: 'lazy' },
  bench: { url: `${import.meta.env.BASE_URL}gltf/estate/bench.glb`, type: AssetType.GLTF, name: 'Banc en chene et fonte — Blender', priority: 'lazy' },
  basin: { url: `${import.meta.env.BASE_URL}gltf/estate/basin.glb`, type: AssetType.GLTF, name: 'Fontaine en calcaire — Blender', priority: 'lazy' },
  water: { url: `${import.meta.env.BASE_URL}gltf/estate/water.glb`, type: AssetType.GLTF, name: 'Eau animee — Blender', priority: 'lazy' },
  lateralJet: { url: `${import.meta.env.BASE_URL}gltf/estate/lateralJet.glb`, type: AssetType.GLTF, name: 'Jet lateral anime — Blender', priority: 'lazy' },
  centralJet: { url: `${import.meta.env.BASE_URL}gltf/estate/centralJet.glb`, type: AssetType.GLTF, name: 'Jet central anime — Blender', priority: 'lazy' },
  arrival: { url: `${import.meta.env.BASE_URL}gltf/arrival-coach/arrival.glb`, type: AssetType.GLTF, name: 'Accueil sculpte avec ouverture — Blender', priority: 'lazy' },
  arrivalWicket: { url: `${import.meta.env.BASE_URL}gltf/arrival-coach/wicket.glb`, type: AssetType.GLTF, name: 'Portillon royal de l accueil', priority: 'lazy' },
  royalCoach: { url: `${import.meta.env.BASE_URL}gltf/arrival-coach/royalCoach.glb?v=20260911-final`, type: AssetType.GLTF, name: 'Voiture royale et deux chevaux', priority: 'lazy' },
  royalCoachAnimated: { url: `${import.meta.env.BASE_URL}gltf/arrival-coach/royalCoachAnimated.glb?v=travel-1`, type: AssetType.GLTF, name: 'Attelage local anime', priority: 'lazy' },
  coachPortal,
  coachTurningCourt: {url:`${import.meta.env.BASE_URL}gltf/arrival-coach/turningCourt.glb`,type:AssetType.GLTF,priority:'lazy',name:'Aire de retournement du carrosse'},
  'coach-panel': {url:`${import.meta.env.BASE_URL}ui/coach.uikitml`,type:AssetType.UIKitML,priority:'lazy'},
  arrivalCollision: createStaticCollision(arrivalCollisionProxy),
  arrivalBoundary,
  arrivalTerrain: {url:`${import.meta.env.BASE_URL}gltf/arrival-landscape/terrain.glb`,type:AssetType.GLTF,priority:'lazy',name:'Prairie etendue de l accueil'},
  arrivalForest: {url:`${import.meta.env.BASE_URL}gltf/arrival-landscape/forest.glb?v=leaf-mask-1`,type:AssetType.GLTF,priority:'lazy',name:'Foret de chenes Blender'},
  arrivalPath: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/arrivalPath.glb?v=arc-2`,type:AssetType.GLTF,priority:'lazy',name:'Chemin de gravier ajuste au cercle'},
  arrivalEstate: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/estateExterior.glb`,type:AssetType.GLTF,priority:'lazy',name:'Domaine lointain sans interieur'},
  royalGate: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/royalGate.glb`,type:AssetType.GLTF,priority:'lazy',name:'Grand portail royal en fer forge'},
  royalGateFar: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/royalGateFar.glb`,type:AssetType.GLTF,priority:'lazy',name:'Portail royal lointain'},
  royalFence: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/royalFence.glb?v=detail-2`,type:AssetType.GLTF,priority:'lazy',name:'Enceinte royale complete et ornee'},
  royalFenceFar: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/royalFenceFar.glb?v=detail-2`,type:AssetType.GLTF,priority:'lazy',name:'Enceinte royale lointaine'},
  royalGateApproach: {url:`${import.meta.env.BASE_URL}gltf/royal-enclosure/gateApproach.glb`,type:AssetType.GLTF,priority:'lazy',name:'Raccord gravier sous le portail'},
  royalEnclosureCollision,
  arrivalLawnRelief: { url: `${import.meta.env.BASE_URL}gltf/vegetation/arrivalLawnRelief.glb`, type: AssetType.GLTF, name: 'Pelouse de l’accueil en relief', priority: 'lazy' },
  'arrival-panel': {url:`${import.meta.env.BASE_URL}ui/arrival.uikitml`,type:AssetType.UIKitML},
  groundCollision: createStaticCollision(ground),
  pathCollision: createStaticCollision(path),
  parterreCollision: createStaticCollision(parterre),
  cypressCollision: createStaticCollision(cypress),
  benchCollision: createStaticCollision(benchCollisionProxy),
  urnCollision: createStaticCollision(urn),
  gardenBorderCollision: createStaticCollision(gardenBorder),
  basinCollision: createStaticCollision(basinCollisionProxy),
  'estate-panel': { url: `${import.meta.env.BASE_URL}ui/estate.uikitml`, type: AssetType.UIKitML },
  'comfort-menu': { url: `${import.meta.env.BASE_URL}ui/comfort.uikitml`, type: AssetType.UIKitML },
});


