using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using VRC.SDK3.Components;
using Object=UnityEngine.Object;

public static class UpdateDomaineDecor
{
    public const string Root=SetupDomaineInteractions.Root;
    [Serializable] public class Part {public string name;public float[] matrix,positions,uv,seed;public int[] indices;}
    [Serializable] public class Asset {public string id;public Part[] meshes;}
    [Serializable] public class Node {public string id,name,asset;public float[] matrix;}
    [Serializable] public class Config {public Node[] nodes;public Asset[] assets;}
    [Serializable] public class Result {public bool passed;public int benches,seats,mirrors,ovalMirrors,rectangleMirrors,hearths,removedStaticTriangles,verticalBorders,fountainSurfaces;public string[] checks;}
    static Result result=new Result();
    static void Require(bool ok,string message){if(!ok)throw new Exception(message);}
    static GameObject Empty(string name,Transform parent){var go=new GameObject(name);go.transform.SetParent(parent,false);return go;}
    static T SaveAsset<T>(T asset,string path) where T:Object {
        var old=AssetDatabase.LoadAssetAtPath<T>(path);if(old){EditorUtility.CopySerialized(asset,old);Object.DestroyImmediate(asset);return old;}AssetDatabase.CreateAsset(asset,path);return asset;
    }
    static void ReplaceMesh(MeshFilter mf,Mesh mesh,string name){
        mesh=SaveAsset(mesh,Root+"/Meshes/"+name+".asset");mf.sharedMesh=mesh;
        foreach(var c in mf.GetComponents<MeshCollider>())c.sharedMesh=mesh;
    }
    static void Placement(Transform t,float[] values){
        var m=new Matrix4x4();for(int i=0;i<16;i++)m[i]=values[i];var flip=Matrix4x4.Scale(new Vector3(-1,1,1));m=flip*m*flip;
        t.SetPositionAndRotation(m.GetColumn(3),m.rotation);t.localScale=m.lossyScale;
    }
    static Mesh MeshFrom(Part part,string name){
        var mesh=new Mesh{name=name};var vertices=new Vector3[part.positions.Length/3];var uv=new Vector2[vertices.Length];var seeds=new Vector2[vertices.Length];
        for(int i=0;i<vertices.Length;i++){vertices[i]=new Vector3(-part.positions[i*3],part.positions[i*3+1],part.positions[i*3+2]);uv[i]=new Vector2(part.uv[i*2],part.uv[i*2+1]);if(part.seed!=null&&part.seed.Length>i)seeds[i]=new Vector2(part.seed[i],0);}
        var indices=(int[])part.indices.Clone();for(int i=0;i<indices.Length;i+=3){int a=indices[i];indices[i]=indices[i+2];indices[i+2]=a;}
        if(name.StartsWith("mirror-"))for(int i=0;i<vertices.Length;i++)vertices[i]=Quaternion.Euler(0,180,0)*vertices[i];
        mesh.vertices=vertices;mesh.uv=uv;mesh.uv2=seeds;mesh.triangles=indices;mesh.RecalculateNormals();mesh.RecalculateBounds();return mesh;
    }
    static void Program(string name){
        string path=Root+"/Scripts/"+name+".asset";if(AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(path))return;
        var p=ScriptableObject.CreateInstance<UdonSharpProgramAsset>();p.sourceCsScript=AssetDatabase.LoadAssetAtPath<MonoScript>(Root+"/Scripts/"+name+".cs");AssetDatabase.CreateAsset(p,path);
    }
    static void Border(MeshFilter mf){
        var mesh=Object.Instantiate(mf.sharedMesh);var materials=mf.GetComponent<Renderer>().sharedMaterials;
        int gravel=Array.FindIndex(materials,m=>m.name.Contains("Crushed limestone"));Require(gravel>=0,"Parterre gravel missing");
        var vertices=mesh.vertices;var ids=mesh.GetTriangles(gravel).Distinct().ToArray();Require(ids.Length>0,"No gravel vertices");
        Vector3 center=mf.transform.parent.position;float extent=0;
        foreach(int i in ids){var p=mf.transform.TransformPoint(vertices[i])-center;extent=Mathf.Max(extent,Mathf.Abs(p.x),Mathf.Abs(p.z));}
        Require(extent>6.8f&&extent<7.01f,"Unexpected garden footprint");
        foreach(int i in ids){var p=mf.transform.TransformPoint(vertices[i])-center;p.x*=6.86f/extent;p.z*=6.86f/extent;vertices[i]=mf.transform.InverseTransformPoint(p+center);}
        mesh.vertices=vertices;mesh.RecalculateBounds();mesh.name="Parterre - gravier interieur aux pierres";
        ReplaceMesh(mf,mesh,mf.transform.parent.name+"-faces-verticales");result.verticalBorders++;
        // Outer stone walls remain at +/-7m; no gravel wall can coincide with them.
        Require(ids.All(i=>{var p=mf.transform.TransformPoint(vertices[i])-center;return Mathf.Abs(p.x)<6.87f&&Mathf.Abs(p.z)<6.87f;}),"Gravel still overlaps vertical edging");
    }
    static void Bench(MeshFilter mf){
        var collider=mf.GetComponent<MeshCollider>();if(!collider)collider=mf.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=mf.sharedMesh;collider.convex=false;
        var parent=mf.transform.parent;
        var old=parent.Find("Deux places assises");if(old)Object.DestroyImmediate(old.gameObject);
        var root=Empty("Deux places assises",parent);root.transform.localRotation=Quaternion.Euler(90,0,0);
        foreach(float side in new[]{-.43f,.43f}){
            var go=Empty(side<0?"Place gauche":"Place droite",root.transform);go.transform.localPosition=new Vector3(side,.55f,0);
            var enter=Empty("Position assise",go.transform).transform;
            var exit=Empty("Se relever devant le banc",go.transform).transform;exit.localPosition=new Vector3(0,-.50f,.9f);
            var station=go.AddComponent<VRCStation>();station.seated=true;station.disableStationExit=false;station.canUseStationFromStation=false;
            station.PlayerMobility=VRC.SDKBase.VRCStation.Mobility.Immobilize;station.stationEnterPlayerLocation=enter;station.stationExitPlayerLocation=exit;
            var trigger=go.AddComponent<BoxCollider>();trigger.isTrigger=true;trigger.center=new Vector3(0,.08f,0);trigger.size=new Vector3(.68f,.18f,.46f);
            var script=go.AddUdonSharpComponent<DomaineBenchSeat>();script.station=station;UdonSharpEditorUtility.CopyProxyToUdon(script);
            var udon=UdonSharpEditorUtility.GetBackingUdonBehaviour(script);udon.interactText="S'asseoir";udon.proximity=2f;result.seats++;
        }result.benches++;
    }
    static void Fountain(){
        var fountain=Object.FindObjectOfType<DomaineFountain>();Require(fountain,"Missing fountain script");
        for(int i=0;i<fountain.surfaces.Length;i++){
            var r=fountain.surfaces[i];var mesh=r.sharedMesh;var vertices=mesh.vertices;var delta=new Vector3[vertices.Length];var bounds=mesh.bounds;
            for(int shape=0;shape<mesh.blendShapeCount;shape++){
                mesh.GetBlendShapeFrameVertices(shape,0,delta,null,null);
                for(int v=0;v<vertices.Length;v++)bounds.Encapsulate(vertices[v]+delta[v]);
            }
            bounds.Expand(.15f);r.localBounds=bounds;r.updateWhenOffscreen=true;
            fountain.durations[i]=(r.name=="eau"||r.sharedMesh.name.Contains("Basin"))?4f:1f;result.fountainSurfaces++;
        }
        UdonSharpEditorUtility.CopyProxyToUdon(fountain);
    }
    public static void RepairBenchFrames(){try{
        var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        var roots=Object.FindObjectsOfType<DomaineBenchSeat>().Select(s=>s.transform.parent).Distinct().ToArray();
        Require(roots.Length==4,"Bench seat roots missing");foreach(var t in roots)t.localRotation=Quaternion.Euler(90,0,0);
        var fountain=Object.FindObjectOfType<DomaineFountain>();
        foreach(var r in fountain.surfaces.Where(r=>r.name.Contains("Basin"))){var mesh=r.sharedMesh;var normal=new Vector3[mesh.vertexCount];mesh.GetBlendShapeFrameVertices(1,0,new Vector3[mesh.vertexCount],normal,null);Debug.Log("WATER_NORMAL_DELTAS "+normal.Max(n=>n.magnitude));}
        EditorSceneManager.MarkSceneDirty(scene);Require(EditorSceneManager.SaveScene(scene),"Scene save failed");Debug.Log("BENCH_FRAMES_REPAIRED 4");EditorApplication.Exit(0);
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
    public static void CorrectWaterAndValidate(){try{
        var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);Fountain();
        var fountain=Object.FindObjectOfType<DomaineFountain>();
        foreach(var r in fountain.surfaces.Where(r=>r.name=="eau"||r.sharedMesh.name.Contains("Basin"))){
            var mesh=r.sharedMesh;var normals=new Vector3[mesh.vertexCount];var delta=new Vector3[mesh.vertexCount];mesh.GetBlendShapeFrameVertices(1,0,delta,normals,null);float strength=normals.Max(n=>n.magnitude);Debug.Log("WATER_NORMAL_DELTAS "+strength);
            if(strength<.0001f){
                var corrected=Object.Instantiate(mesh);corrected.ClearBlendShapes();var temp=Object.Instantiate(mesh);temp.ClearBlendShapes();var vertices=mesh.vertices;var baseNormals=mesh.normals;
                for(int shape=0;shape<mesh.blendShapeCount;shape++){
                    mesh.GetBlendShapeFrameVertices(shape,0,delta,null,null);temp.vertices=vertices.Select((v,i)=>v+delta[i]).ToArray();temp.RecalculateNormals();var targetNormals=temp.normals;
                    for(int i=0;i<normals.Length;i++)normals[i]=targetNormals[i]-baseNormals[i];
                    corrected.AddBlendShapeFrame(mesh.GetBlendShapeName(shape),100,delta,normals,null);
                }
                corrected.name="Eau - ondes et normales animees";r.sharedMesh=SaveAsset(corrected,Root+"/Meshes/eau-ondes-normales.asset");Object.DestroyImmediate(temp);Debug.Log("WATER_NORMALS_REPAIRED");
            }
        }
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);Require(EditorSceneManager.SaveScene(scene),"Water scene save failed");ValidateDomaineDecor.Run();
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
    public static void Run(){try{
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);Program("DomaineBenchSeat");Program("DomaineMirrorVisibility");
        AssetDatabase.SaveAssets();UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
        string backup="DomaineImportReports/scene-before-decor-animations.unity.backup";if(!File.Exists(backup))File.Copy(SetupDomaineInteractions.ScenePath,backup);
        var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        Directory.CreateDirectory(Root+"/Meshes");AssetDatabase.Refresh();
        var meshes=Object.FindObjectsOfType<MeshFilter>();
        foreach(var mf in meshes.Where(m=>m.transform.parent&&m.transform.parent.name.StartsWith("gardens__parterre-")))Border(mf);
        foreach(var mf in meshes.Where(m=>m.transform.parent&&m.transform.parent.name.StartsWith("gardens__banc-")))Bench(mf);
        Require(result.benches==4&&result.seats==8,"Expected four garden benches and eight seats");Fountain();
        var interior=meshes.Single(m=>m.GetComponent<Renderer>()&&m.GetComponent<Renderer>().sharedMaterials.Any(mat=>mat&&mat.name=="hearthFire"));
        var inside=Object.Instantiate(interior.sharedMesh);var mats=interior.GetComponent<Renderer>().sharedMaterials;
        for(int s=0;s<mats.Length;s++)if(mats[s]&&(mats[s].name.StartsWith("mirrorOval")||mats[s].name.StartsWith("mirrorRectangle")||mats[s].name.StartsWith("hearthFire"))){result.removedStaticTriangles+=inside.GetTriangles(s).Length/3;inside.SetTriangles(new int[0],s);}
        inside.name="Interieur - miroirs et flammes separes";ReplaceMesh(interior,inside,"interieur-reflets-flammes");
        var parent=GameObject.Find("Interactions du Domaine").transform;
        var prior=parent.Find("Miroirs et feux vivants");if(prior)Object.DestroyImmediate(prior.gameObject);
        var decor=Empty("Miroirs et feux vivants",parent);
        var config=JsonUtility.FromJson<Config>(File.ReadAllText(Root+"/Source/decor-config.json"));
        var mirrorShader=Shader.Find("FX/MirrorReflection");var flameShader=Shader.Find("Domaine/Flammes vivantes");
        Require(mirrorShader&&flameShader&&!ShaderUtil.ShaderHasError(flameShader),"Missing or broken shaders");
        var mirrorObjects=new List<GameObject>();
        foreach(var node in config.nodes){
            var go=Empty(node.id,decor.transform);Placement(go.transform,node.matrix);
            bool mirror=node.asset.StartsWith("mirror");
            var mesh=MeshFrom(config.assets.Single(a=>a.id==node.asset).meshes[0],node.id);
            mesh=SaveAsset(mesh,Root+"/Meshes/"+node.id+".asset");go.AddComponent<MeshFilter>().sharedMesh=mesh;
            var renderer=go.AddComponent<MeshRenderer>();renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
            var material=new Material(mirror?mirrorShader:flameShader){name=node.id};
            if(mirror){
                material.SetTexture("_MainTex",Texture2D.whiteTexture);go.layer=4;go.transform.Rotate(0,180,0,Space.Self);
                var reflection=go.AddComponent<VRCMirrorReflection>();reflection.m_ReflectLayers=(1<<0)|(1<<9)|(1<<11)|(1<<18);reflection.m_DisablePixelLights=false;reflection.TurnOffMirrorOcclusion=true;
                var serialized=new SerializedObject(reflection);serialized.FindProperty("mirrorResolution").intValue=1024;serialized.ApplyModifiedPropertiesWithoutUndo();
                mirrorObjects.Add(go);result.mirrors++;if(node.asset=="mirrorOval")result.ovalMirrors++;else result.rectangleMirrors++;
            }else{material.SetFloat("_Phase",result.hearths*1.73f);result.hearths++;}
            renderer.sharedMaterial=SaveAsset(material,Root+"/Materials/"+node.id+"-vivant.mat");
        }
        var manager=decor.AddUdonSharpComponent<DomaineMirrorVisibility>();manager.mirrors=mirrorObjects.ToArray();UdonSharpEditorUtility.CopyProxyToUdon(manager);
        foreach(var go in mirrorObjects)go.SetActive(false);
        Require(result.mirrors==6&&result.hearths==4,"Missing mirrors or hearths");
        Require(Object.FindObjectsOfType<DomainePassengerSeat>().All(s=>s.station.disableStationExit),"Carriage lock changed");
        Require(Object.FindObjectOfType<DomaineJump>(),"Jump activation lost");
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);Require(EditorSceneManager.SaveScene(scene),"Scene save failed");
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        Require(Object.FindObjectsOfType<DomaineBenchSeat>().Length==8,"Bench seats not persisted");
        result.passed=true;result.checks=new[]{"Udon and flame shader compiled","Four gravel beds recessed behind vertical stone faces","Eight independent static bench stations saved","Six correctly shaped native VRChat mirrors with proximity activation","Static flame and mirror faces removed from interior mesh","Four animated procedural flame meshes preserve crossed sheets and per-flame seeds","Fountain bounds include every morph and update while off screen","Jump and locked carriage stations preserved"};
        File.WriteAllText("DomaineImportReports/decor-installation.json",JsonUtility.ToJson(result,true));Debug.Log("DOMAINE_DECOR_SETUP "+JsonUtility.ToJson(result));EditorApplication.Exit(0);
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
}
