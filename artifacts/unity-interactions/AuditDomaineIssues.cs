using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using Object=UnityEngine.Object;

public static class AuditDomaineIssues
{
    [Serializable] public class MeshInfo { public string path,mesh,asset;public string[] materials;public Vector3 center,size,localPosition,localRotation,localScale;public int vertices,triangles;public string[] colliders; }
    [Serializable] public class WheelInfo {public string name,path;public Vector3 position,rotation,scale,boundsCenter,boundsSize,worldAxle,meshCenter,meshSize;}
    [Serializable] public class Report { public string[] roots;public MeshInfo[] meshes;public WheelInfo[] wheels;public string[] wheelCurves;public string[] colliders; }
    public static string PathOf(Transform t){string p=t.name;while(t.parent){t=t.parent;p=t.name+"/"+p;}return p;}
    public static void Run(){try{
        var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        var coach=Object.FindObjectOfType<DomaineLocalCoach>();
        var curves=new List<string>();
        foreach(string file in new[]{"carrosse-HorseIdle","carrosse-HorseWalk"})
            foreach(var clip in AssetDatabase.LoadAllAssetsAtPath(SetupDomaineInteractions.Root+"/Models/"+file+".fbx").OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview")))
                foreach(var b in AnimationUtility.GetCurveBindings(clip).Where(b=>b.path.Contains("Wheel")))curves.Add(file+" "+b.path+" "+b.propertyName);
        var report=new Report {
            roots=scene.GetRootGameObjects().Select(g=>g.name).ToArray(),
            meshes=Object.FindObjectsOfType<MeshFilter>().Select(m=>new MeshInfo{path=PathOf(m.transform),mesh=m.sharedMesh.name,asset=AssetDatabase.GetAssetPath(m.sharedMesh),
                materials=m.GetComponent<Renderer>()?m.GetComponent<Renderer>().sharedMaterials.Select(x=>x?x.name:"NULL").ToArray():new string[0],
                center=m.GetComponent<Renderer>()?m.GetComponent<Renderer>().bounds.center:Vector3.zero,size=m.GetComponent<Renderer>()?m.GetComponent<Renderer>().bounds.size:Vector3.zero,
                localPosition=m.transform.localPosition,localRotation=m.transform.localEulerAngles,localScale=m.transform.localScale,
                vertices=m.sharedMesh.vertexCount,triangles=m.sharedMesh.triangles.Length/3,colliders=m.GetComponents<Collider>().Select(c=>c.GetType().Name+" enabled="+c.enabled).ToArray()}).ToArray(),
            wheels=coach.wheels.Select(w=>new WheelInfo{name=w.name,path=PathOf(w),position=w.localPosition,rotation=w.localEulerAngles,scale=w.localScale,
                boundsCenter=coach.carriage.InverseTransformPoint(w.GetComponent<Renderer>().bounds.center),boundsSize=w.GetComponent<Renderer>().bounds.size,
                worldAxle=w.TransformDirection(Vector3.forward),meshCenter=w.GetComponent<MeshFilter>().sharedMesh.bounds.center,meshSize=w.GetComponent<MeshFilter>().sharedMesh.bounds.size}).ToArray(),
            wheelCurves=curves.ToArray(),colliders=Object.FindObjectsOfType<Collider>().Select(c=>PathOf(c.transform)+" "+c.GetType().Name+" trigger="+c.isTrigger+" bounds="+c.bounds).ToArray()
        };
        File.WriteAllText("DomaineImportReports/audit-corrections.json",JsonUtility.ToJson(report,true));
        ValidateDomaineInteractions.Preview("audit-jardin.png",new Vector3(-118,7,-85),new Vector3(-100,0,-98),70);
        ValidateDomaineInteractions.Preview("audit-chateau.png",new Vector3(-100,2.4f,-119),new Vector3(-99,1,-126),88);
        Debug.Log("DOMAINE_AUDIT "+report.meshes.Length+" meshes, "+report.wheelCurves.Length+" wheel animation bindings");EditorApplication.Exit(0);
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
}
