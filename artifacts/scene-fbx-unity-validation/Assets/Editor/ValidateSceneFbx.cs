using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class ValidateSceneFbx {
    [Serializable] public class Result {
        public string file;
        public int meshes;
        public long triangles;
        public bool interiorIsSeparate;
        public string interiorObjectName;
        public Vector3 interiorMin;
        public Vector3 interiorMax;
        public bool passed;
    }
    [Serializable] public class Report { public string unityVersion; public Result[] files; public bool interiorAligned; }
    public static void Run() {
        try {
            var results=new[] {"scene-complete.fbx","interieur-chateau.fbx"}.Select(file=>{
                string path="Assets/Domaine/"+file;
                var importer=(ModelImporter)AssetImporter.GetAtPath(path);
                importer.isReadable=true;
                importer.importAnimation=false;
                importer.SaveAndReimport();
                var model=AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if(model==null) throw new Exception("FBX import failed: "+file);
                var instance=(GameObject)PrefabUtility.InstantiatePrefab(model);
                var meshes=instance.GetComponentsInChildren<MeshFilter>(true);
                // Unity names a standalone model's root after its FBX filename.
                var interior=file=="interieur-chateau.fbx"&&meshes.Length==1 ? meshes[0] : meshes.SingleOrDefault(m=>m.name=="Interieur_Chateau");
                var bounds=interior ? interior.GetComponent<Renderer>().bounds : new Bounds();
                bool finite=meshes.All(m=>m.sharedMesh.vertices.All(v=>!float.IsNaN(v.x)&&!float.IsNaN(v.y)&&!float.IsNaN(v.z)&&!float.IsInfinity(v.x)&&!float.IsInfinity(v.y)&&!float.IsInfinity(v.z)));
                var result=new Result { file=file,meshes=meshes.Length,triangles=meshes.Sum(m=>(long)m.sharedMesh.triangles.Length/3),
                    interiorIsSeparate=interior!=null,interiorObjectName=interior?interior.name:null,interiorMin=bounds.min,interiorMax=bounds.max,
                    passed=finite&&interior!=null&&(file!="interieur-chateau.fbx"||meshes.Length==1)};
                UnityEngine.Object.DestroyImmediate(instance);
                Debug.Log("SCENE_FBX_CHECK "+JsonUtility.ToJson(result));return result;
            }).ToArray();
            bool aligned=Vector3.Distance(results[0].interiorMin,results[1].interiorMin)<.002f&&Vector3.Distance(results[0].interiorMax,results[1].interiorMax)<.002f;
            File.WriteAllText("../scene-fbx/verification-unity.json",JsonUtility.ToJson(new Report {unityVersion=Application.unityVersion,files=results,interiorAligned=aligned},true));
            EditorApplication.Exit(results.All(r=>r.passed)&&aligned?0:2);
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
}
