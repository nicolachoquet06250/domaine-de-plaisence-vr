using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharpEditor;
using VRC.SDKBase;
using VRC.Udon;
using VRC.SDK3.ClientSim;
using Object=UnityEngine.Object;

[InitializeOnLoad]
public static class ValidateDomaineInteractions
{
    const string Key="Domaine.RuntimeValidation";
    static int step;
    static double began, stepAt, stoppedAt;
    static DomaineNetworkDoor door;
    static DomaineLocalCoach coach;
    static UdonBehaviour coachUdon;
    static Vector3 initialPosition;
    static float[] initialWaterWeights;
    static Quaternion initialHoofRotation;
    static Transform hoof;
    static List<string> checks=new List<string>();
    static List<string> errors=new List<string>();
    static bool stopping;
    [Serializable] public class Result { public bool passed;public string[] checks,errors;public string mode="Unity ClientSim / actual Udon runtime";public bool liveMultiplayerTested=false; }
    static ValidateDomaineInteractions() {
        if(SessionState.GetBool(Key,false)) { began=EditorApplication.timeSinceStartup;stepAt=began;EditorApplication.update+=Tick;Application.logMessageReceived+=Log; }
    }
    public static void Run() {
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        var settings=ClientSimSettings.Instance;settings.enableClientSim=true;settings.spawnPlayer=true;settings.localPlayerIsMaster=true;settings.hideMenuOnLaunch=true;
        SessionState.SetBool(Key,true);began=EditorApplication.timeSinceStartup;stepAt=began;
        EditorApplication.update-=Tick;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;
        EditorApplication.isPlaying=true;
    }
    static void Log(string condition,string trace,LogType type) {
        if(errors.Count<20 && (type==LogType.Error||type==LogType.Exception)&& (condition.Contains("Udon")||trace.Contains("Domaine")) && !errors.Contains(condition))errors.Add(condition);
    }
    static void Next(string passed) { checks.Add(passed);Debug.Log("DOMAINE_RUNTIME_CHECK "+passed);step++;stepAt=EditorApplication.timeSinceStartup;stoppedAt=0; }
    static bool Riding() { return (bool)coachUdon.GetProgramVariable("riding"); }
    static bool AtCastle() { return (bool)coachUdon.GetProgramVariable("atCastle"); }
    static void Tick() {
        if(stopping) {
            if(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode)EditorApplication.Exit(errors.Count==0?0:1);
            return;
        }
        try {
            double now=EditorApplication.timeSinceStartup;
            if(now-began>360)throw new Exception("ClientSim validation timeout at step "+step);
            if(!EditorApplication.isPlaying||!Utilities.IsValid(Networking.LocalPlayer))return;
            float elapsed=(float)(now-stepAt);
            if(step==0) {
                if(elapsed<12)return;
                door=Object.FindObjectsOfType<DomaineNetworkDoor>().Single(d=>d.name=="castle/door-entrance");
                coach=Object.FindObjectOfType<DomaineLocalCoach>();coachUdon=UdonSharpEditorUtility.GetBackingUdonBehaviour(coach);
                var allocation=Object.FindObjectOfType<DomaineSeatAllocation>();var ids=(int[])UdonSharpEditorUtility.GetBackingUdonBehaviour(allocation).GetProgramVariable("passengerIds");
                if(ids.Count(id=>id==Networking.LocalPlayer.playerId)!=1)throw new Exception("Local passenger does not have one unique station");
                foreach(var menu in Object.FindObjectsOfType<ClientSimMenu>())menu.WarningAccepted();
                var water=Object.FindObjectOfType<DomaineFountain>();initialWaterWeights=Enumerable.Range(0,8).Select(i=>water.surfaces[0].GetBlendShapeWeight(i)).ToArray();
                Networking.LocalPlayer.TeleportTo(door.transform.TransformPoint(new Vector3(0,.05f,2)),Quaternion.Euler(0,180,0));
                Next("Local player initialized; unique passenger station allocated");
            } else if(step==1&&elapsed>3) {
                if(Quaternion.Angle(door.leftHinge.localRotation,Quaternion.identity)<100||door.doorwayBlocker.enabled)throw new Exception("Door failed to open automatically in Udon");
                Preview("porte-ouverte.png",new Vector3(-100,2.5f,-110),new Vector3(-100,2.3f,-120),65);
                Networking.LocalPlayer.TeleportTo(new Vector3(0,.2f,2),Quaternion.identity);
                Next("Owner proximity opens door; passage collider disabled");
            } else if(step==2&&elapsed>4) {
                if(Quaternion.Angle(door.leftHinge.localRotation,Quaternion.identity)>.5f||!door.doorwayBlocker.enabled)throw new Exception("Door failed to close after leaving");
                var water=Object.FindObjectOfType<DomaineFountain>();
                if(!Enumerable.Range(0,8).Any(i=>Mathf.Abs(water.surfaces[0].GetBlendShapeWeight(i)-initialWaterWeights[i])>.1f))throw new Exception("Water morphs not advancing at runtime");
                Preview("fontaine-animee.png",new Vector3(-109,5,-86),new Vector3(-100,1,-95),58);
                coachUdon.SendCustomEvent("BoardAtArrival");initialPosition=coach.carriage.position;
                hoof=coach.horses.GetComponentsInChildren<Transform>().First(t=>t.name.Contains("FrontLFoot"));initialHoofRotation=hoof.localRotation;
                Next("Door closes and collision returns after delay; fountain has active morphs");
            } else if(step==3&&elapsed>5) {
                if(!Riding())throw new Exception("Boarding failed");
                if(Vector3.Distance(initialPosition,coach.carriage.position)<2)throw new Exception("Coach did not move");
                if(Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.seatAnchor.position)>1)throw new Exception("Passenger station does not follow coach");
                if(Mathf.Abs(Networking.LocalPlayer.GetTrackingData(VRCPlayerApi.TrackingDataType.Head).position.y-coach.carriage.position.y-coach.seatViewHeight)>.2f)throw new Exception("Passenger viewpoint is outside the cabin");
                if(Quaternion.Angle(initialHoofRotation,hoof.localRotation)<.1f)throw new Exception("Horse walking clip not moving bones");
                Preview("carrosse-en-voyage.png",coach.carriage.position+new Vector3(7,4,8),coach.carriage.position+Vector3.up*1.8f,60);
                Next("Local boarding, moving passenger, horse animation and outbound movement verified");
            } else if(step==4&&!Riding()&&elapsed>2) {
                if(stoppedAt==0){stoppedAt=now;return;}if(now-stoppedAt<1)return;
                if(!AtCastle()||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.castleDrop.position)>1)throw new Exception("Outbound arrival did not disembark at castle");
                coachUdon.SendCustomEvent("BoardAtCastle");Next("Full outbound trip: automatic castle disembarkation");
            } else if(step==5&&elapsed>5) {
                if(!Riding())throw new Exception("Return boarding failed");
                Next("Return boarding and forecourt U-turn started");
            } else if(step==6&&!Riding()&&elapsed>2) {
                if(stoppedAt==0){stoppedAt=now;return;}if(now-stoppedAt<1)return;
                if(AtCastle()||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.arrivalDrop.position)>1)throw new Exception("Return arrival incorrect");
                coachUdon.SendCustomEvent("BoardAtArrival");Next("Full return trip: automatic reception disembarkation");
            } else if(step==7&&elapsed>4) {
                if(!Riding())throw new Exception("Repeated boarding failed");
                coachUdon.SendCustomEvent("ExitRide");Next("Early exit requested during a new journey");
            } else if(step==8&&elapsed>2) {
                if(Riding()||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.arrivalDrop.position)>1)throw new Exception("Early exit failed");
                Next("Early exit restores player at safe terminal; coach reusable");
                ClientSimMain.SpawnRemotePlayer("Passager test A");ClientSimMain.SpawnRemotePlayer("Passager test B");
            } else if(step==9&&elapsed>3) {
                var allocation=Object.FindObjectOfType<DomaineSeatAllocation>();
                var ids=(int[])UdonSharpEditorUtility.GetBackingUdonBehaviour(allocation).GetProgramVariable("passengerIds");
                if(ids.Count(id=>id!=0)!=3||ids.Where(id=>id!=0).Distinct().Count()!=3)throw new Exception("Passengers share an allocated station");
                for(int i=0;i<ids.Length;i++)if(ids[i]!=0&&Networking.GetOwner(allocation.seats[i].gameObject).playerId!=ids[i])throw new Exception("Passenger station ownership incorrect");
                if(Riding())throw new Exception("Remote arrival changed local coach state");
                var players=new VRCPlayerApi[100];VRCPlayerApi.GetPlayers(players);
                foreach(var player in players)if(Utilities.IsValid(player)&&!player.isLocal)ClientSimMain.RemovePlayer(player);
                Next("Three simulated players receive distinct stations; local coach state remains independent");
            } else if(step==10&&elapsed>4) {
                var allocation=Object.FindObjectOfType<DomaineSeatAllocation>();var ids=(int[])UdonSharpEditorUtility.GetBackingUdonBehaviour(allocation).GetProgramVariable("passengerIds");
                if(ids.Count(id=>id!=0)!=1)throw new Exception("Departed passengers did not release their allocations");
                Next("Departed players release station allocations");Finish();
            }
        }catch(Exception ex){errors.Add(ex.ToString());Debug.LogException(ex);Finish();}
    }
    static void Finish() {
        if(stopping)return;stopping=true;SessionState.SetBool(Key,false);
        var result=new Result{passed=errors.Count==0,checks=checks.ToArray(),errors=errors.ToArray()};
        File.WriteAllText("DomaineImportReports/interactions-runtime.json",JsonUtility.ToJson(result,true));
        Debug.Log("DOMAINE_RUNTIME_RESULT "+JsonUtility.ToJson(result));
        // No runtime state is saved into the authored scene.
        EditorApplication.isPlaying=false;
        EditorApplication.delayCall+=()=>EditorApplication.Exit(result.passed?0:1);
    }
    public static void Preview(string filename,Vector3 position,Vector3 target,float fov) {
        var go=new GameObject("Camera validation");var camera=go.AddComponent<Camera>();camera.transform.position=position;camera.transform.LookAt(target);
        camera.fieldOfView=fov;camera.nearClipPlane=.05f;camera.farClipPlane=500;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.5f,.6f,.7f);
        var rt=new RenderTexture(1400,950,24);camera.targetTexture=rt;camera.Render();var previous=RenderTexture.active;RenderTexture.active=rt;
        var picture=new Texture2D(1400,950,TextureFormat.RGB24,false);picture.ReadPixels(new Rect(0,0,1400,950),0,0);picture.Apply();
        File.WriteAllBytes("DomaineImportReports/"+filename,picture.EncodeToPNG());RenderTexture.active=previous;camera.targetTexture=null;
        Object.DestroyImmediate(picture);rt.Release();Object.DestroyImmediate(rt);Object.DestroyImmediate(go);
    }
}
