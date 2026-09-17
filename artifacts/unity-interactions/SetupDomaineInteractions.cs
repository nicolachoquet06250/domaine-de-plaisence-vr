using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using VRC.SDK3.Components;
using Object = UnityEngine.Object;

public static class SetupDomaineInteractions
{
    public const string Root = "Assets/DomainePlaisance/Interactions";
    public const string ScenePath = "Assets/DomainePlaisance/Scenes/Domaine de Plaisance.unity";
    [Serializable] public class Placement { public string id, asset; public float[] matrix; }
    [Serializable] public class Route { public string name; public float length; public Vector3[] points; }
    [Serializable] public class Morph { public string asset, node; public float duration; }
    [Serializable] public class TextureSpec { public string name, baseTexture, normalTexture; }
    [Serializable] public class Config { public Placement[] placements; public Route[] routes; public Morph[] morphs; public TextureSpec[] coachMaterials; }
    [Serializable] public class MatSpec { public string name; public float[] color; public float metallic, roughness; public bool vertexColor; }
    [Serializable] public class AssetSpec { public string name; public MatSpec[] materials; }
    [Serializable] public class AssetReport { public int removedInteriorDoorFaces; public AssetSpec[] assets; }
    [Serializable] public class Result {
        public bool passed, udonCompiled, interiorDoorGeometryRemoved, allMaterialsAssigned, independentPassengerSeats;
        public int doors, animatedWaterMeshes, shapeKeys, passengerSeats, routeSamples;
        public float outboundMeters, inboundMeters;
        public string scene, multiplayerTest;
    }
    static string Safe(string s) { foreach(char c in Path.GetInvalidFileNameChars()) s=s.Replace(c,'_'); return s; }
    static GameObject Empty(string name, Transform parent=null) { var go=new GameObject(name); if(parent)go.transform.SetParent(parent,false); return go; }
    static GameObject Model(string name, Transform parent) {
        var asset=AssetDatabase.LoadAssetAtPath<GameObject>(Root+"/Models/"+name+".fbx");
        if(!asset)throw new Exception("Missing model "+name);
        var go=(GameObject)PrefabUtility.InstantiatePrefab(asset);
        PrefabUtility.UnpackPrefabInstance(go,PrefabUnpackMode.Completely,InteractionMode.AutomatedAction);
        go.transform.SetParent(parent,false); return go;
    }
    static void SetPlacement(Transform t, Placement p) {
        Matrix4x4 m=new Matrix4x4();for(int i=0;i<16;i++)m[i]=p.matrix[i];
        var reflect=Matrix4x4.Scale(new Vector3(-1,1,1)); m=reflect*m*reflect;
        t.position=m.GetColumn(3);t.rotation=m.rotation;t.localScale=m.lossyScale;
    }
    static void Remap(string name, Dictionary<string,Material> materials, bool animate=false) {
        string path=Root+"/Models/"+name+".fbx";
        var importer=(ModelImporter)AssetImporter.GetAtPath(path);
        importer.importAnimation=animate;importer.animationType=ModelImporterAnimationType.Generic;
        importer.isReadable=true;importer.importBlendShapes=true;importer.importCameras=false;importer.importLights=false;
        importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;importer.SaveAndReimport();
        foreach(var m in AssetDatabase.LoadAllAssetsAtPath(path).OfType<Material>()) {
            if(!materials.TryGetValue(m.name,out Material mapped))throw new Exception("Material unmapped "+name+": "+m.name);
            importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material),m.name),mapped);
        }
        if(animate) { var clips=importer.defaultClipAnimations;foreach(var clip in clips){clip.loopTime=true;clip.loopPose=true;}importer.clipAnimations=clips; }
        importer.SaveAndReimport();
    }
    static Material SaveMat(Material mat,string name) {
        string path=Root+"/Materials/"+Safe(name)+".mat";var existing=AssetDatabase.LoadAssetAtPath<Material>(path);
        if(existing){EditorUtility.CopySerialized(mat,existing);Object.DestroyImmediate(mat);return existing;}
        AssetDatabase.CreateAsset(mat,path);return mat;
    }
    static TextMesh Label(string text,Transform parent,Vector3 position,float size=.1f) {
        var go=Empty(text,parent);go.transform.localPosition=position;
        var label=go.AddComponent<TextMesh>();label.text=text;label.fontSize=48;label.characterSize=size;
        label.anchor=TextAnchor.MiddleCenter;label.alignment=TextAlignment.Center;label.color=new Color(1,.87f,.55f);
        return label;
    }
    static GameObject Button(string text,Transform parent,Vector3 position,DomaineLocalCoach coach,int action) {
        var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=text;go.transform.SetParent(parent,false);
        go.transform.localPosition=position;go.transform.localScale=new Vector3(1.6f,.5f,.12f);
        var material=AssetDatabase.LoadAssetAtPath<Material>(Root+"/Materials/Panneaux.mat");go.GetComponent<Renderer>().sharedMaterial=material;
        var behaviour=go.AddUdonSharpComponent<DomaineCoachButton>();behaviour.coach=coach;behaviour.action=action;
        var udon=UdonSharpEditorUtility.GetBackingUdonBehaviour(behaviour);udon.interactText=text;udon.proximity=3f;
        var label=Label(text,parent,position+new Vector3(0,0,-.071f),.052f);
        label.transform.SetParent(go.transform,true);
        return go;
    }
    public static void Run() {
        try {
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Directory.CreateDirectory(Root+"/Materials");Directory.CreateDirectory(Root+"/Animation");Directory.CreateDirectory("DomaineImportReports");
            var config=JsonUtility.FromJson<Config>(File.ReadAllText(Root+"/Source/interaction-config.json"));
            var report=JsonUtility.FromJson<AssetReport>(File.ReadAllText(Root+"/Source/assets-report.json"));
            foreach(string file in Directory.GetFiles(Root+"/Scripts","*.cs")) {
                string scriptPath=file.Replace('\\','/');string programPath=Path.ChangeExtension(scriptPath,"asset");
                if(AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(programPath))continue;
                var program=ScriptableObject.CreateInstance<UdonSharpProgramAsset>();
                program.sourceCsScript=AssetDatabase.LoadAssetAtPath<MonoScript>(scriptPath);
                AssetDatabase.CreateAsset(program,programPath);
            }
            AssetDatabase.SaveAssets();UdonSharpProgramAsset.CompileAllCsPrograms(true);
            foreach(string file in Directory.GetFiles(Root+"/Scripts","*.asset")) {
                var program=AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(file.Replace('\\','/'));
                if(program&&program.SerializedProgramAsset.RetrieveProgram()==null)throw new Exception("Udon program not compiled: "+file);
            }
            var materials=AssetDatabase.FindAssets("t:Material",new[]{"Assets/DomainePlaisance/Materials"})
                .Select(g=>AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(g))).ToDictionary(m=>m.name);
            Remap("interieur-sans-portes",materials);Remap("portes-mobiles",materials);
            foreach(var asset in report.assets) {
                var map=new Dictionary<string,Material>();
                foreach(var s in asset.materials) {
                    // Water retains the previously verified materials and textures.
                    Material mat=null;
                    if(asset.name!="carrosse") {
                        string oldName=s.name+(asset.name=="jet-central"?".001":"");materials.TryGetValue(oldName,out mat);
                    }
                    if(!mat) {
                        mat=new Material(Shader.Find("Domaine/PBR Vertex"));mat.name=s.name;
                        mat.SetColor("_Color",new Color(s.color[0],s.color[1],s.color[2],1).gamma);
                        mat.SetFloat("_Metallic",s.metallic);mat.SetFloat("_Glossiness",1-s.roughness);mat.SetFloat("_UseVertexColor",s.vertexColor?1:0);
                        var texture=config.coachMaterials.FirstOrDefault(t=>t.name==s.name);
                        if(texture!=null) {
                            if(!string.IsNullOrEmpty(texture.normalTexture)) {
                                string p=Root+"/Textures/"+texture.normalTexture;var ti=(TextureImporter)AssetImporter.GetAtPath(p);
                                ti.textureType=TextureImporterType.NormalMap;ti.SaveAndReimport();mat.SetTexture("_BumpMap",AssetDatabase.LoadAssetAtPath<Texture2D>(p));
                            }
                            if(!string.IsNullOrEmpty(texture.baseTexture))mat.SetTexture("_MainTex",AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Textures/"+texture.baseTexture));
                        }
                        mat=SaveMat(mat,asset.name+"_"+s.name);
                    }
                    map[s.name]=mat;
                }
                if(asset.name=="carrosse"){Remap("carrosse-HorseIdle",map,true);Remap("carrosse-HorseWalk",map,true);}
                else Remap(asset.name,map);
            }
            var scene=EditorSceneManager.OpenScene(ScenePath,OpenSceneMode.Single);
            var oldInteractions=GameObject.Find("Interactions du Domaine");
            if(oldInteractions)throw new Exception("Interactions already installed: use validation instead of replacing authored changes.");
            var domain=GameObject.Find("Domaine de Plaisance");
            if(PrefabUtility.IsPartOfPrefabInstance(domain))PrefabUtility.UnpackPrefabInstance(domain,PrefabUnpackMode.Completely,InteractionMode.AutomatedAction);
            var inside=domain.GetComponentsInChildren<MeshFilter>(true).Single(m=>m.name=="Interieur_Chateau");
            Object.DestroyImmediate(inside.GetComponent<MeshCollider>());Object.DestroyImmediate(inside.GetComponent<MeshRenderer>());Object.DestroyImmediate(inside);
            var root=Empty("Interactions du Domaine");
            var interior=Model("interieur-sans-portes",root.transform);interior.name="Interieur du chateau - sans portes mobiles";
            foreach(var mesh in interior.GetComponentsInChildren<MeshFilter>())mesh.gameObject.AddComponent<MeshCollider>().sharedMesh=mesh.sharedMesh;
            var oldTransforms=domain.GetComponentsInChildren<Transform>(true);
            foreach(var t in oldTransforms)if(t && (t.name=="castle__door-entrance"||t.name=="arrival-coach"||t.name=="coach-departure"||t.name=="coach-return"||t.name=="fountain__water"||t.name.StartsWith("fountain__jet-")))Object.DestroyImmediate(t.gameObject);
            var doors=new List<DomaineNetworkDoor>();
            foreach(var p in config.placements.Where(p=>p.asset=="palaceDoor")) {
                var door=Empty(p.id,root.transform);var model=Model("portes-mobiles",door.transform);
                var script=door.AddUdonSharpComponent<DomaineNetworkDoor>();
                var left=Empty("Charniere gauche",door.transform).transform;left.localPosition=new Vector3(1.6f,0,0);
                var right=Empty("Charniere droite",door.transform).transform;right.localPosition=new Vector3(-1.6f,0,0);
                foreach(var mesh in model.GetComponentsInChildren<MeshFilter>()) {
                    mesh.transform.SetParent(mesh.name.Contains("Left")?left:right,true);
                    mesh.gameObject.AddComponent<MeshCollider>().sharedMesh=mesh.sharedMesh;
                }
                Object.DestroyImmediate(model);script.leftHinge=left;script.rightHinge=right;
                var blocker=door.AddComponent<BoxCollider>();blocker.center=new Vector3(0,1.65f,0);blocker.size=new Vector3(3.2f,3.3f,.18f);script.doorwayBlocker=blocker;
                SetPlacement(door.transform,p);doors.Add(script);
                UdonSharpEditorUtility.GetBackingUdonBehaviour(script).interactText="Ouvrir les portes";
            }
            var fountain=Empty("Fontaine animee",root.transform).AddUdonSharpComponent<DomaineFountain>();
            var surfaces=new List<SkinnedMeshRenderer>();var durations=new List<float>();var phases=new List<float>();
            foreach(var p in config.placements.Where(p=>p.asset!="palaceDoor")) {
                string asset=p.asset=="water"?"eau":p.asset=="centralJet"?"jet-central":"jet-lateral";
                var placement=Empty(p.id,fountain.transform);var model=Model(asset,placement.transform);SetPlacement(placement.transform,p);
                foreach(var r in model.GetComponentsInChildren<SkinnedMeshRenderer>()) {
                    r.updateWhenOffscreen=false;surfaces.Add(r);
                    durations.Add(config.morphs.First(m=>m.asset==p.asset).duration);
                    phases.Add(p.asset=="lateralJet"?surfaces.Count*.31f:0f);
                }
            }
            fountain.surfaces=surfaces.ToArray();fountain.durations=durations.ToArray();fountain.phases=phases.ToArray();
            var coach=Empty("Carrosse personnel",root.transform).AddUdonSharpComponent<DomaineLocalCoach>();
            coach.carriage=Empty("Attelage local",coach.transform).transform;
            var coachModel=Model("carrosse-HorseIdle",coach.carriage);
            var animator=coachModel.GetComponent<Animator>();if(!animator)animator=coachModel.AddComponent<Animator>();
            animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
            string controllerPath=Root+"/Animation/Carrosse.controller";
            var controller=AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
            foreach(string clipName in new[]{"HorseIdle","HorseWalk"}) {
                var clip=AssetDatabase.LoadAllAssetsAtPath(Root+"/Models/carrosse-"+clipName+".fbx").OfType<AnimationClip>().First(c=>!c.name.StartsWith("__preview"));
                var state=controller.layers[0].stateMachine.AddState(clipName);state.motion=clip;
            }
            animator.runtimeAnimatorController=controller;coach.horses=animator;
            var coachTransforms=coachModel.GetComponentsInChildren<Transform>();
            coach.wheels=new[]{"WheelFrontL","WheelFrontR","WheelRearL","WheelRearR"}.Select(n=>coachTransforms.Single(t=>t.name==n)).ToArray();
            coach.seatAnchor=Empty("Place du passager",coach.carriage).transform;
            coach.seatAnchor.localPosition=new Vector3(.6f,1.05f,0);coach.seatAnchor.localRotation=Quaternion.Euler(0,-90,0);
            coach.arrivalDrop=Empty("Sortie accueil",root.transform).transform;coach.arrivalDrop.position=new Vector3(-5.4f,.2f,0);coach.arrivalDrop.rotation=Quaternion.Euler(0,90,0);
            coach.castleDrop=Empty("Sortie chateau",root.transform).transform;coach.castleDrop.position=new Vector3(-100,.25f,-70);coach.castleDrop.rotation=Quaternion.Euler(0,180,0);
            coach.outbound=config.routes.Single(r=>r.name=="outbound").points;coach.inbound=config.routes.Single(r=>r.name=="inbound").points;
            coach.outboundLength=config.routes.Single(r=>r.name=="outbound").length;coach.inboundLength=config.routes.Single(r=>r.name=="inbound").length;
            coach.Place(0,false);
            var allocator=Empty("Places individuelles VRChat",root.transform).AddUdonSharpComponent<DomaineSeatAllocation>();coach.allocation=allocator;
            allocator.seats=new DomainePassengerSeat[100];
            for(int i=0;i<100;i++) {
                var slot=Empty("Place passager "+i,allocator.transform);slot.transform.position=new Vector3(0,-5,0);
                var station=slot.AddComponent<VRC.SDK3.Components.VRCStation>();station.PlayerMobility=VRC.SDKBase.VRCStation.Mobility.ImmobilizeForVehicle;
                station.seated=true;station.disableStationExit=true;station.canUseStationFromStation=false;
                station.stationEnterPlayerLocation=slot.transform;station.stationExitPlayerLocation=slot.transform;
                var rb=slot.AddComponent<Rigidbody>();rb.isKinematic=true;rb.useGravity=false;
                var sync=slot.AddComponent<VRCObjectSync>();sync.AllowCollisionOwnershipTransfer=false;
                var passenger=slot.AddUdonSharpComponent<DomainePassengerSeat>();passenger.station=station;passenger.poseSync=sync;passenger.coach=coach;allocator.seats[i]=passenger;
            }
            var boardMat=new Material(Shader.Find("Standard"));boardMat.color=new Color(.08f,.035f,.017f);SaveMat(boardMat,"Panneaux");
            var arrivalPanel=Empty("Depart royal",root.transform);arrivalPanel.transform.position=new Vector3(-7.15f,1.3f,0);arrivalPanel.transform.rotation=Quaternion.Euler(0,-90,0);
            Button("Monter - vers le chateau",arrivalPanel.transform,Vector3.zero,coach,0);
            var returnPanel=Empty("Retour royal",root.transform);returnPanel.transform.position=new Vector3(-100,1.3f,-65.5f);returnPanel.transform.rotation=Quaternion.identity;
            Button("Monter - retour a l'accueil",returnPanel.transform,Vector3.zero,coach,1);
            var cabinPanel=Empty("Commandes du passager",coach.carriage);cabinPanel.transform.localPosition=new Vector3(-.1f,1.85f,0);cabinPanel.transform.localRotation=Quaternion.Euler(0,-90,0);
            var canvasGo=Empty("Information du voyage",cabinPanel.transform);
            canvasGo.transform.localPosition=new Vector3(0,.5f,0);canvasGo.transform.localScale=Vector3.one*.003f;
            var canvas=canvasGo.AddComponent<Canvas>();canvas.renderMode=RenderMode.WorldSpace;
            var textGo=new GameObject("Destination",typeof(RectTransform));textGo.transform.SetParent(canvasGo.transform,false);
            var rect=(RectTransform)textGo.transform;rect.sizeDelta=new Vector2(700,100);
            coach.status=textGo.AddComponent<UnityEngine.UI.Text>();coach.status.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            coach.status.fontSize=24;coach.status.alignment=TextAnchor.MiddleCenter;coach.status.text="Carrosse royal";coach.status.color=new Color(1,.87f,.55f);
            // Save all references into Udon program variables, including proxy arrays.
            foreach(var b in root.GetComponentsInChildren<UdonSharpBehaviour>(true))UdonSharpEditorUtility.CopyProxyToUdon(b);
            ValidateGeometry(doors,fountain,coach);
            foreach(var b in root.GetComponentsInChildren<UdonSharpBehaviour>(true))UdonSharpEditorUtility.CopyProxyToUdon(b);
            AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(scene,ScenePath);
            var result=new Result {passed=true,udonCompiled=true,interiorDoorGeometryRemoved=report.removedInteriorDoorFaces==4960,
                allMaterialsAssigned=root.GetComponentsInChildren<Renderer>(true).All(r=>r.sharedMaterials.All(m=>m&&m.shader)),
                independentPassengerSeats=allocator.seats.Distinct().Count()==100,doors=doors.Count,animatedWaterMeshes=surfaces.Count,
                shapeKeys=surfaces.Sum(r=>r.sharedMesh.blendShapeCount),passengerSeats=100,routeSamples=coach.outbound.Length+coach.inbound.Length,
                outboundMeters=coach.outboundLength,inboundMeters=coach.inboundLength,scene=ScenePath,
                multiplayerTest="Requires two VRChat clients; editor checks do not prove live network synchronization."};
            File.WriteAllText("DomaineImportReports/interactions-setup.json",JsonUtility.ToJson(result,true));
            Debug.Log("DOMAINE_INTERACTIONS_SETUP "+JsonUtility.ToJson(result));EditorApplication.Exit(0);
        } catch(Exception ex) {Debug.LogException(ex);EditorApplication.Exit(1);}
    }
    public static void RepairAndTest() {
        try {
            EditorSceneManager.OpenScene(ScenePath,OpenSceneMode.Single);
            UdonSharpProgramAsset.CompileAllCsPrograms(true);
            foreach(var slot in Object.FindObjectsOfType<DomainePassengerSeat>())slot.transform.position=new Vector3(0,-5,0);
            var coach=Object.FindObjectOfType<DomaineLocalCoach>();coach.seatAnchor.localPosition=new Vector3(.6f,1.05f,0);
            GameObject.Find("Retour royal").transform.rotation=Quaternion.identity;
            GameObject.Find("Commandes du passager").transform.localPosition=new Vector3(-.1f,1.85f,0);
            foreach(var script in Object.FindObjectsOfType<UdonSharp.UdonSharpBehaviour>())UdonSharpEditorUtility.CopyProxyToUdon(script);
            EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());AssetDatabase.SaveAssets();
            ValidateDomaineInteractions.Run();
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
    static void ValidateGeometry(List<DomaineNetworkDoor> doors,DomaineFountain fountain,DomaineLocalCoach coach) {
        foreach(var d in doors) {
            d.ApplyProgress(0);if(!d.doorwayBlocker.enabled)throw new Exception("Closed door has no blocker");
            d.ApplyProgress(1);if(d.doorwayBlocker.enabled||Quaternion.Angle(d.leftHinge.localRotation,Quaternion.identity)<90)throw new Exception("Door does not open");
            d.ApplyProgress(0);
        }
        fountain.SampleTime(.2);float first=fountain.surfaces[0].GetBlendShapeWeight(0);fountain.SampleTime(.8);
        if(Mathf.Approximately(first,fountain.surfaces[0].GetBlendShapeWeight(0)))throw new Exception("Water morphs not animated");
        if(coach.outbound.Length!=2049||coach.inbound.Length!=2049)throw new Exception("Incomplete route");
        if(Vector3.Distance(coach.Point(coach.outboundLength,false),coach.Point(0,true))>.01f)throw new Exception("Discontinuous return route");
        foreach(var renderer in coach.carriage.GetComponentsInChildren<SkinnedMeshRenderer>())if(renderer.bones.Length==0)throw new Exception("Horse skin missing bones");
        foreach(var shader in Object.FindObjectsOfType<Renderer>().SelectMany(r=>r.sharedMaterials).Where(m=>m).Select(m=>m.shader).Distinct())
            if(ShaderUtil.ShaderHasError(shader))throw new Exception("Shader failed "+shader.name);
    }
}
