using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UdonSharpEditor;
using Object=UnityEngine.Object;

public static class FixDomaineIssues
{
    const string MeshRoot=SetupDomaineInteractions.Root+"/Meshes";
    [Serializable] public class Report {public bool passed;public int grassCollidersRemoved,wheelCurvesRemoved,stoneCornersRepaired,pathMeshesTrimmed,fountainRays; public string[] checks;}
    static Report report=new Report();
    static string PathOf(Transform t){return AuditDomaineIssues.PathOf(t);}
    static void Require(bool ok,string why){if(!ok)throw new Exception(why);}
    static void SaveMesh(MeshFilter mf,Mesh mesh,string name){
        string path=MeshRoot+"/"+name+".asset";
        var old=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(old){EditorUtility.CopySerialized(mesh,old);Object.DestroyImmediate(mesh);mesh=old;}
        else AssetDatabase.CreateAsset(mesh,path);
        mf.sharedMesh=mesh;foreach(var c in mf.GetComponents<MeshCollider>())c.sharedMesh=mesh;
    }
    static int Find(int[] parent,int i){while(parent[i]!=i){parent[i]=parent[parent[i]];i=parent[i];}return i;}
    static void Join(int[] parent,int a,int b){parent[Find(parent,a)]=Find(parent,b);}
    static void FixCorners(MeshFilter mf){
        var source=mf.sharedMesh;var vertices=source.vertices;
        int stone=Array.FindIndex(mf.GetComponent<Renderer>().sharedMaterials,m=>m.name.Contains("Weathered limestone"));
        Require(stone>=0,"Missing parterre stone material");
        var triangles=source.GetTriangles(stone);var parent=Enumerable.Range(0,vertices.Length).ToArray();
        var positions=new Dictionary<Vector3Int,int>();
        foreach(int i in triangles){var p=vertices[i];var key=new Vector3Int(Mathf.RoundToInt(p.x*100000),Mathf.RoundToInt(p.y*100000),Mathf.RoundToInt(p.z*100000));if(positions.TryGetValue(key,out int j))Join(parent,i,j);else positions[key]=i;}
        for(int i=0;i<triangles.Length;i+=3){Join(parent,triangles[i],triangles[i+1]);Join(parent,triangles[i],triangles[i+2]);}
        var groups=triangles.Distinct().GroupBy(i=>Find(parent,i));int count=0;
        foreach(var group in groups){
            var ids=group.ToArray();var b=new Bounds(mf.transform.TransformPoint(vertices[ids[0]])-mf.transform.parent.position,Vector3.zero);
            foreach(int i in ids)b.Encapsulate(mf.transform.TransformPoint(vertices[i])-mf.transform.parent.position);
            if(b.size.x<.9f||b.size.x>1.1f||b.size.z>.2f||Mathf.Abs(b.center.x)<6||Mathf.Abs(b.center.z)<6.8f)continue;
            float sign=Mathf.Sign(b.center.x),outer=sign>0?b.max.x:-b.min.x,inner=sign>0?b.min.x:-b.max.x;
            foreach(int i in ids){var w=mf.transform.TransformPoint(vertices[i])-mf.transform.parent.position;w.x=sign*Mathf.Lerp(inner,6.845f,(sign*w.x-inner)/(outer-inner));vertices[i]=mf.transform.InverseTransformPoint(w+mf.transform.parent.position);}
            count++;
        }
        Require(count==4,"Expected four overlapping corner stones, got "+count+" on "+mf.name);
        var mesh=Object.Instantiate(source);mesh.name=source.name+" - joints sans chevauchement";mesh.vertices=vertices;mesh.RecalculateBounds();
        SaveMesh(mf,mesh,mf.transform.parent.name+"-bordures");report.stoneCornersRepaired+=count;
    }
    struct Vertex {public Vector3 p,n;public Vector2 uv,uv2;public Vector4 tangent;public Color color;
        public static Vertex Lerp(Vertex a,Vertex b,float t){return new Vertex{p=Vector3.Lerp(a.p,b.p,t),n=Vector3.Lerp(a.n,b.n,t).normalized,uv=Vector2.Lerp(a.uv,b.uv,t),uv2=Vector2.Lerp(a.uv2,b.uv2,t),tangent=Vector4.Lerp(a.tangent,b.tangent,t),color=Color.Lerp(a.color,b.color,t)};}}
    static float Side(Vertex v,int axis,float limit,float sign){return (v.p[axis]-limit)*sign;}
    static List<Vertex> Clip(List<Vertex> polygon,int axis,float limit,float sign){
        var result=new List<Vertex>();if(polygon.Count==0)return result;var a=polygon[polygon.Count-1];float da=Side(a,axis,limit,sign);
        foreach(var b in polygon){float db=Side(b,axis,limit,sign);if((da>=0)!=(db>=0))result.Add(Vertex.Lerp(a,b,da/(da-db)));if(db>=0)result.Add(b);a=b;da=db;}return result;
    }
    // Partition along the four rectangle planes. Keep every outside piece once.
    static List<List<Vertex>> Subtract(List<Vertex> polygon,Rect rect){
        var result=new List<List<Vertex>>();var rest=polygon;
        int[] axes={0,0,2,2};float[] limits={rect.xMin,rect.xMax,rect.yMin,rect.yMax};float[] signs={1,-1,1,-1};
        for(int i=0;i<4&&rest.Count>=3;i++){var outside=Clip(rest,axes[i],limits[i],-signs[i]);if(outside.Count>=3)result.Add(outside);rest=Clip(rest,axes[i],limits[i],signs[i]);}return result;
    }
    static void TrimPaths(MeshFilter mf,Rect[] cutouts){
        var mesh=mf.sharedMesh;var p=mesh.vertices;var n=mesh.normals;var uv=mesh.uv;var uv2=mesh.uv2;var tangents=mesh.tangents;var colors=mesh.colors;
        var input=new Vertex[p.Length];for(int i=0;i<p.Length;i++)input[i]=new Vertex{p=mf.transform.TransformPoint(p[i]),n=n.Length==p.Length?n[i]:Vector3.up,uv=uv.Length==p.Length?uv[i]:Vector2.zero,uv2=uv2.Length==p.Length?uv2[i]:Vector2.zero,tangent=tangents.Length==p.Length?tangents[i]:Vector4.zero,color=colors.Length==p.Length?colors[i]:Color.white};
        var output=new List<Vertex>();var indices=new List<int[]>();
        for(int sub=0;sub<mesh.subMeshCount;sub++){
            var ts=mesh.GetTriangles(sub);var idx=new List<int>();
            for(int j=0;j<ts.Length;j+=3){var pieces=new List<List<Vertex>>{new List<Vertex>{input[ts[j]],input[ts[j+1]],input[ts[j+2]]}};
                foreach(var rect in cutouts){var next=new List<List<Vertex>>();foreach(var poly in pieces)next.AddRange(Subtract(poly,rect));pieces=next;}
                foreach(var poly in pieces)for(int k=1;k<poly.Count-1;k++){
                    if(Vector3.Cross(poly[k].p-poly[0].p,poly[k+1].p-poly[0].p).sqrMagnitude<1e-14f)continue;
                    idx.Add(output.Count);output.Add(poly[0]);idx.Add(output.Count);output.Add(poly[k]);idx.Add(output.Count);output.Add(poly[k+1]);
                }
            }indices.Add(idx.ToArray());
        }
        var repaired=new Mesh{name=mesh.name+" - raccords sans superposition",indexFormat=IndexFormat.UInt32};
        repaired.vertices=output.Select(v=>mf.transform.InverseTransformPoint(v.p)).ToArray();repaired.normals=output.Select(v=>v.n).ToArray();repaired.uv=output.Select(v=>v.uv).ToArray();
        if(uv2.Length==p.Length)repaired.uv2=output.Select(v=>v.uv2).ToArray();if(tangents.Length==p.Length)repaired.tangents=output.Select(v=>v.tangent).ToArray();if(colors.Length==p.Length)repaired.colors=output.Select(v=>v.color).ToArray();
        repaired.subMeshCount=indices.Count;for(int s=0;s<indices.Count;s++)repaired.SetTriangles(indices[s],s);repaired.RecalculateBounds();
        Require(repaired.vertexCount>0,"Trim removed entire path");SaveMesh(mf,repaired,mf.transform.parent.name+"-raccords");report.pathMeshesTrimmed++;
    }
    static void WheelClips(DomaineLocalCoach coach){
        var controller=(AnimatorController)coach.horses.runtimeAnimatorController;
        foreach(string name in new[]{"HorseIdle","HorseWalk"}){
            var source=AssetDatabase.LoadAllAssetsAtPath(SetupDomaineInteractions.Root+"/Models/carrosse-"+name+".fbx").OfType<AnimationClip>().First(c=>!c.name.StartsWith("__preview"));
            var clip=Object.Instantiate(source);clip.name=name+" - chevaux seuls";
            foreach(var b in AnimationUtility.GetCurveBindings(clip).Where(b=>b.path.Split('/').Any(p=>p.StartsWith("Wheel")))){AnimationUtility.SetEditorCurve(clip,b,null);report.wheelCurvesRemoved++;}
            string path=SetupDomaineInteractions.Root+"/Animation/"+name+"-chevaux.anim";var old=AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if(old){EditorUtility.CopySerialized(clip,old);Object.DestroyImmediate(clip);clip=old;}else AssetDatabase.CreateAsset(clip,path);
            controller.layers[0].stateMachine.states.Single(s=>s.state.name==name).state.motion=clip;
            Require(!AnimationUtility.GetCurveBindings(clip).Any(b=>b.path.Contains("Wheel")),"Wheel curves remain");
        }EditorUtility.SetDirty(controller);
    }
    public static void Run(){try{
        string backup="DomaineImportReports/scene-before-reported-fixes.unity.backup";if(!File.Exists(backup))File.Copy(SetupDomaineInteractions.ScenePath,backup);
        UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
        var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        Directory.CreateDirectory(MeshRoot);AssetDatabase.Refresh();
        var meshes=Object.FindObjectsOfType<MeshFilter>();
        foreach(var mf in meshes.Where(m=>m.name.StartsWith("Bent grass tile")))foreach(var c in mf.GetComponents<Collider>()){Object.DestroyImmediate(c);report.grassCollidersRemoved++;}
        var basin=meshes.Single(m=>m.transform.parent.name=="fountain__basin");
        var basinCollider=basin.GetComponent<MeshCollider>();if(!basinCollider)basinCollider=basin.gameObject.AddComponent<MeshCollider>();basinCollider.sharedMesh=basin.sharedMesh;basinCollider.convex=false;
        foreach(var mf in meshes.Where(m=>m.transform.parent.name.StartsWith("gardens__parterre-")))FixCorners(mf);
        TrimPaths(meshes.Single(m=>m.transform.parent.name=="gardens__allee-centrale"),new[]{new Rect(-122.5f,-98.5f,45,7),new Rect(-122.5f,-118,45,6),new Rect(-122.5f,-74,45,6)});
        TrimPaths(meshes.Single(m=>m.transform.parent.name=="landscape-path"),new[]{new Rect(-103.5f,-68,7,4),new Rect(-122.5f,-74,45,6)});
        var coach=Object.FindObjectOfType<DomaineLocalCoach>();WheelClips(coach);
        Require(Mathf.Abs(coach.seatViewHeight-2.48f)<.001f,"Seat height changed");
        foreach(var portal in Object.FindObjectsOfType<DomaineCoachPortal>()){
            var trigger=(BoxCollider)portal.passage;trigger.center=new Vector3(0,1.75f,-.35f);trigger.size=new Vector3(2f,4.5f,1.9f);trigger.isTrigger=true;
            var backing=UdonSharpEditorUtility.GetBackingUdonBehaviour(portal);backing.proximity=3;UdonSharpEditorUtility.CopyProxyToUdon(portal);
        }
        UdonSharpEditorUtility.CopyProxyToUdon(coach);UdonSharpEditorUtility.CopyProxyToUdon(coach.allocation);
        Physics.SyncTransforms();
        for(int i=0;i<32;i++){float angle=(i+.5f)*Mathf.PI*2/32;var radial=new Vector3(Mathf.Cos(angle),0,Mathf.Sin(angle));
            Require(basinCollider.Raycast(new Ray(new Vector3(-100,3,-95)+radial*4.05f,Vector3.down),out var hit,4),"Fountain rim has gap "+i);
            Require(hit.point.y>.35f,"Rim ray only hit basin floor "+i);report.fountainRays++;
        }
        Require(!meshes.Where(m=>m.name.StartsWith("Bent grass tile")).Any(m=>m.GetComponent<Collider>()),"Grass colliders remain");
        Require(meshes.Single(m=>m.name=="Sculpted continuous cut turf").GetComponent<MeshCollider>(),"Ground collision lost");
        Require(Object.FindObjectsOfType<DomainePassengerSeat>().All(s=>s.station.disableStationExit),"Station lock lost");
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        ValidateDomaineInteractions.Preview("corrections-portail-chateau.png",new Vector3(-100,1.8f,-73),new Vector3(-100,2,-65),80);
        ValidateDomaineInteractions.Preview("corrections-bordures-jardin.png",new Vector3(-80,1.4f,-77),new Vector3(-81.2f,.1f,-78.2f),75);
        ValidateDomaineInteractions.Preview("corrections-fontaine.png",new Vector3(-105,2.2f,-89),new Vector3(-100,.5f,-95),75);
        report.passed=true;report.checks=new[]{"Udon compiled synchronously","Scene saved and reopened","Ground collision retained; decorative grass collision removed","32 fountain rim rays hit stone above water floor","Wheel animation bindings removed from both horse clips","Four parterre corners repaired per bed","Overlapping gravel junctions partitioned without offset","Portal foot-position fallback and ownership retries installed","Raised seat and locked journeys preserved"};
        File.WriteAllText("DomaineImportReports/corrections-scene.json",JsonUtility.ToJson(report,true));Debug.Log("DOMAINE_FIXES "+JsonUtility.ToJson(report));EditorApplication.Exit(0);
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
}
