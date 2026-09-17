using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharpEditor;
using VRC.SDKBase;
using VRC.SDK3.Components;
using VRC.Udon;
using Object=UnityEngine.Object;

[InitializeOnLoad]
public static class ValidateDomaineDecor
{
    const string Key="Domaine.DecorValidation";
    static double start,changed;
    static int step,seatIndex,waterSamples;
    static bool ending;
    static float[] lastWeights;
    static DomaineFountain fountain;
    static DomaineBenchSeat[] seats;
    static DomaineMirrorVisibility visibility;
    static List<string> checks=new List<string>(),errors=new List<string>();
    [Serializable] public class Result {public bool passed,liveVRChatTested;public int seatsTested,fountainChanges;public string[] checks,errors;}
    static ValidateDomaineDecor(){if(SessionState.GetBool(Key,false)){start=changed=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;}}
    static void Require(bool ok,string message){if(!ok)throw new Exception(message);}
    static void Log(string message,string stack,LogType type){if(errors.Count<12&&(type==LogType.Error||type==LogType.Exception)&&(message.Contains("Udon")||stack.Contains("Domaine")))errors.Add(message);}
    static float[] Weights(DomaineFountain f){return f.surfaces.SelectMany(r=>Enumerable.Range(0,r.sharedMesh.blendShapeCount).Select(r.GetBlendShapeWeight)).ToArray();}
    static void CheckWeights(float[] values){Require(values.All(v=>!float.IsNaN(v)&&v>=-.001f&&v<=100.001f),"Invalid fountain blend weights");}
    public static void Run(){try{
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        var f=Object.FindObjectOfType<DomaineFountain>();Require(f&&f.surfaces.Length==15,"Fountain incomplete");
        foreach(double t in new[]{-4294967.295,-4.001,-.001,0,.137,3.999,4.001,99999999.137}){f.SampleTime(t);CheckWeights(Weights(f));foreach(var r in f.surfaces)Require(Mathf.Abs(Enumerable.Range(0,r.sharedMesh.blendShapeCount).Sum(r.GetBlendShapeWeight)-100)<.01f,"Fountain morph weights do not sum to 100");}
        f.SampleTime(.137);var a=Weights(f);f.SampleTime(4.137);var b=Weights(f);Require(a.Zip(b,(x,y)=>Mathf.Abs(x-y)).Max()<.01f,"Fountain loop does not repeat");
        var first=new Mesh();var second=new Mesh();
        foreach(var r in f.surfaces){f.SampleTime(.137);r.BakeMesh(first);f.SampleTime(.371);r.BakeMesh(second);Require(first.vertices.Zip(second.vertices,(x,y)=>Vector3.Distance(x,y)).Max()>.001f,"Water geometry not animated: "+r.name);Require(r.updateWhenOffscreen,"Water can freeze off screen");}
        Object.DestroyImmediate(first);Object.DestroyImmediate(second);
        var benches=Object.FindObjectsOfType<MeshFilter>().Where(m=>m.transform.parent&&m.transform.parent.name.StartsWith("gardens__banc-")).ToArray();
        Physics.SyncTransforms();foreach(var bench in benches){var c=bench.GetComponent<MeshCollider>();Require(c,"Bench has no collider");foreach(var seat in bench.transform.parent.GetComponentsInChildren<DomaineBenchSeat>()){var origin=seat.station.stationEnterPlayerLocation.position+Vector3.up*2;Require(c.Raycast(new Ray(origin,Vector3.down),out var hit,3),"Bench seat ray missed wood");Require(Mathf.Abs(hit.point.y-seat.station.stationEnterPlayerLocation.position.y)<.08f,"Seat does not align with wood");}}
        var mirrorManager=Object.FindObjectOfType<DomaineMirrorVisibility>();Require(mirrorManager.mirrors.Length==6,"Mirror count");
        foreach(var go in mirrorManager.mirrors){var mirror=go.GetComponent<VRCMirrorReflection>();Require(mirror&&mirror.m_ReflectLayers.value==(1|512|2048|262144),"Mirror reflection layers");var mf=go.GetComponent<MeshFilter>();Require(Vector3.Dot(mf.sharedMesh.normals[0],Vector3.back)>.99f,"Mirror mesh does not follow native quad orientation");}
        RenderPreviews();
        File.WriteAllText("DomaineImportReports/decor-static-validation.json","{\"passed\":true,\"loopAndNegativeTimes\":true,\"animatedWaterMeshes\":15,\"benchCollisionRays\":8,\"mirrorShapes\":6}");
        // Restore authored state after rendering and direct sampling, without saving tests.
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        SessionState.SetBool(Key,true);start=changed=EditorApplication.timeSinceStartup;EditorApplication.update-=Tick;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;EditorApplication.isPlaying=true;
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
    static Texture2D Render(Camera camera){var rt=new RenderTexture(640,480,24);camera.targetTexture=rt;camera.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var tex=new Texture2D(640,480,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,640,480),0,0);tex.Apply();RenderTexture.active=previous;camera.targetTexture=null;rt.Release();Object.DestroyImmediate(rt);return tex;}
    static void RenderPreviews(){
        ValidateDomaineInteractions.Preview("murets-verticaux-corriges.png",new Vector3(-80, .22f,-77),new Vector3(-81.4f,.10f,-80),74);
        ValidateDomaineInteractions.Preview("banc-deux-places.png",new Vector3(-99,1.5f,-101),new Vector3(-96.95f,.55f,-103),65);
        var fires=Object.FindObjectsOfType<MeshRenderer>().Where(r=>r.sharedMaterial&&r.sharedMaterial.shader.name=="Domaine/Flammes vivantes").ToArray();Require(fires.Length==4,"Four fireplace flame renderers required");
        var fire=fires.Single(r=>r.name=="hearth-west-salon-flames");var go=new GameObject("Flame verification camera");var camera=go.AddComponent<Camera>();camera.transform.position=new Vector3(-82.4f,1.28f,-123);camera.transform.LookAt(new Vector3(-80.16f,1.3f,-123));camera.fieldOfView=46;camera.nearClipPlane=.02f;
        fire.sharedMaterial.SetFloat("_TestTime",0);var a=Render(camera);fire.sharedMaterial.SetFloat("_TestTime",.53f);var b=Render(camera);var p=a.GetPixels32();var q=b.GetPixels32();int changedPixels=Enumerable.Range(0,p.Length).Count(i=>Mathf.Abs(p[i].r-q[i].r)+Mathf.Abs(p[i].g-q[i].g)+Mathf.Abs(p[i].b-q[i].b)>20);Require(changedPixels>150,"Flames not visibly animated: "+changedPixels);
        File.WriteAllBytes("DomaineImportReports/cheminee-flammes-0.png",a.EncodeToPNG());File.WriteAllBytes("DomaineImportReports/cheminee-flammes-1.png",b.EncodeToPNG());fire.sharedMaterial.SetFloat("_TestTime",-1);Object.DestroyImmediate(a);Object.DestroyImmediate(b);Object.DestroyImmediate(go);
        var mirrors=Object.FindObjectOfType<DomaineMirrorVisibility>().mirrors;foreach(var m in mirrors)m.SetActive(true);
        ValidateDomaineInteractions.Preview("miroir-rectangulaire.png",new Vector3(-83,3,-122.7f),new Vector3(-80.075f,3.17f,-123),55);
        ValidateDomaineInteractions.Preview("miroir-ovale.png",new Vector3(-93,6.9f,-126),new Vector3(-93,7.07f,-128.163f),50);
        foreach(var m in mirrors)m.SetActive(false);
    }
    static void Next(string check){checks.Add(check);Debug.Log("DOMAINE_DECOR_CHECK "+check);step++;changed=EditorApplication.timeSinceStartup;}
    static void Tick(){if(ending)return;try{
        double now=EditorApplication.timeSinceStartup,elapsed=now-changed;if(now-start>160)throw new Exception("Decor test timeout step "+step);
        if(!EditorApplication.isPlaying||!Utilities.IsValid(Networking.LocalPlayer))return;
        if(step==0&&elapsed>12){
            fountain=Object.FindObjectOfType<DomaineFountain>();seats=Object.FindObjectsOfType<DomaineBenchSeat>().OrderBy(s=>s.transform.parent.parent.name).ThenBy(s=>s.name).ToArray();visibility=Object.FindObjectOfType<DomaineMirrorVisibility>();
            Require(seats.Length==8&&seats.All(s=>!s.station.disableStationExit),"Bench seats should allow standing up");
            lastWeights=Weights(fountain);Next("Eight independent bench stations allow normal exit");
        }else if(step==1){
            var weights=Weights(fountain);CheckWeights(weights);if(weights.Zip(lastWeights,(x,y)=>Mathf.Abs(x-y)).Max()>.01f)waterSamples++;lastWeights=weights;
            if(elapsed>13){Require(waterSamples>30,"Fountain freezes in runtime");Next("Fountain changes continuously across three complete ripple loops while player is at arrival");}
        }else if(step==2){
            if(elapsed<.5)return;
            if(seatIndex==seats.Length){Next("All eight bench stations can be entered and exited");return;}
            var seat=seats[seatIndex];Networking.LocalPlayer.TeleportTo(seat.station.stationExitPlayerLocation.position,seat.station.stationExitPlayerLocation.rotation);UdonSharpEditorUtility.GetBackingUdonBehaviour(seat).Interact();step=3;changed=now;
        }else if(step==3&&seatIndex<seats.Length&&elapsed>1){
            var seat=seats[seatIndex];Require(Vector3.Distance(Networking.LocalPlayer.GetPosition(),seat.station.stationEnterPlayerLocation.position)<.7f,"Bench seating failed "+seat.name);
            seat.station.ExitStation(Networking.LocalPlayer);step=4;changed=now;
        }else if(step==4&&elapsed>1){
            var seat=seats[seatIndex];Require(Vector3.Distance(Networking.LocalPlayer.GetPosition(),seat.station.stationExitPlayerLocation.position)<.7f,"Bench exit failed");seatIndex++;step=2;changed=now;
        }else if(step==3&&seatIndex==seats.Length){
            // Next above advances step 2 to 3 once all stations have been visited.
            var mirror=visibility.mirrors.Single(g=>g.name=="mirror-west-salon");Networking.LocalPlayer.TeleportTo(new Vector3(-83,.8f,-123),Quaternion.identity);step=5;changed=now;
        }else if(step==5&&elapsed>1){
            Require(visibility.mirrors.Single(g=>g.name=="mirror-west-salon").activeSelf,"Nearby mirror not enabled");Require(!visibility.mirrors.Single(g=>g.name=="mirror-east-salon").activeSelf,"Distant mirror renders unnecessarily");
            Networking.LocalPlayer.TeleportTo(new Vector3(0,.12f,2),Quaternion.identity);Next("Mirror activates on approach; distant mirror remains off");
        }else if(step==6&&elapsed>1){
            Require(visibility.mirrors.All(m=>!m.activeSelf),"Mirrors remain active at arrival");Require(Mathf.Abs(Networking.LocalPlayer.GetJumpImpulse()-3.5f)<.001f,"Jump lost");Next("Mirrors deactivate at distance; jump retained");Finish();
        }
    }catch(Exception ex){errors.Add(ex.ToString());Debug.LogException(ex);Finish();}}
    static void Finish(){ending=true;SessionState.SetBool(Key,false);EditorApplication.update-=Tick;
        var result=new Result{passed=errors.Count==0,seatsTested=seatIndex,fountainChanges=waterSamples,checks=checks.ToArray(),errors=errors.ToArray(),liveVRChatTested=false};File.WriteAllText("DomaineImportReports/decor-runtime-validation.json",JsonUtility.ToJson(result,true));Debug.Log("DOMAINE_DECOR_RESULT "+JsonUtility.ToJson(result));EditorApplication.isPlaying=false;EditorApplication.delayCall+=()=>EditorApplication.Exit(result.passed?0:1);
    }
}
