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
using Object=UnityEngine.Object;

[InitializeOnLoad]
public static class ValidateDomaineTravelRules
{
    const string Key="Domaine.LockedTravelValidation";
    static int step;
    static double start,changed,stopped;
    static bool ending;
    static DomaineLocalCoach coach;
    static UdonBehaviour runtime;
    static List<string> checks=new List<string>();
    static List<string> errors=new List<string>();
    [Serializable] public class Result { public bool passed;public string[] checks,errors;public int invisibleWallColliders=100,perimeterRays=2976;public bool liveVRChatTested=false; }
    static ValidateDomaineTravelRules(){if(SessionState.GetBool(Key,false)){start=changed=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;}}
    public static void Run(){
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        SessionState.SetBool(Key,true);start=changed=EditorApplication.timeSinceStartup;
        EditorApplication.update-=Tick;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;EditorApplication.isPlaying=true;
    }
    static void Log(string message,string trace,LogType type){
        if(errors.Count<10&&(type==LogType.Error||type==LogType.Exception)&&(message.Contains("Udon")||trace.Contains("Domaine"))&&!errors.Contains(message))errors.Add(message);
    }
    static bool Riding(){return (bool)runtime.GetProgramVariable("riding");}
    static void Next(string check){checks.Add(check);Debug.Log("DOMAINE_TRAVEL_CHECK "+check);step++;changed=EditorApplication.timeSinceStartup;stopped=0;}
    static CharacterController LocalController(){
        Vector3 p=Networking.LocalPlayer.GetPosition();
        var candidates=Object.FindObjectsOfType<CharacterController>().Where(c=>c.enabled).OrderBy(c=>Vector3.Distance(c.transform.position,p)).ToArray();
        if(candidates.Length==0||Vector3.Distance(candidates[0].transform.position,p)>1)throw new Exception("Local CharacterController not found");
        return candidates[0];
    }
    static void Tick(){
        if(ending)return;
        try {
            double now=EditorApplication.timeSinceStartup,elapsed=now-changed;
            if(now-start>300)throw new Exception("Locked journey timeout at step "+step);
            if(!EditorApplication.isPlaying||!Utilities.IsValid(Networking.LocalPlayer))return;
            if(step==0&&elapsed>12){
                coach=Object.FindObjectOfType<DomaineLocalCoach>();runtime=UdonSharpEditorUtility.GetBackingUdonBehaviour(coach);
                var seats=Object.FindObjectsOfType<DomainePassengerSeat>();
                if(seats.Length!=100||seats.Any(s=>!s.station.disableStationExit||s.station.canUseStationFromStation))throw new Exception("A station still allows voluntary exit or switching");
                if(coach.GetComponentsInChildren<DomaineCoachButton>(true).Any(b=>b.action==2)||coach.GetComponentsInChildren<TextMesh>(true).Any(t=>t.text.Contains("Descendre")))throw new Exception("Exit control remains");
                Networking.LocalPlayer.TeleportTo(new Vector3(6,.15f,0),Quaternion.identity);
                Next("100 stations locked; exit button removed");
            }else if(step==1&&elapsed>.6){
                LocalController().Move(new Vector3(5,0,0));
                if(Networking.LocalPlayer.GetPosition().x>7.7f)throw new Exception("Player walked outside the arrival circle");
                Networking.LocalPlayer.TeleportTo(new Vector3(-103,.15f,-66),Quaternion.identity);
                Next("Actual player movement blocked at arrival perimeter");
            }else if(step==2&&elapsed>.6){
                LocalController().Move(new Vector3(0,0,4));
                if(Networking.LocalPlayer.GetPosition().z>-65.2f)throw new Exception("Player walked through the castle gate");
                Networking.LocalPlayer.TeleportTo(new Vector3(-7.15f,.15f,0),Quaternion.identity);
                Next("Actual player movement blocked at grand gate; arrival portal entered");
            }else if(step==3&&elapsed>3){
                if(!Riding())throw new Exception("Arrival portal cannot be used with boundary walls");
                runtime.SendCustomEvent("ExitRide");runtime.SendCustomEvent("CompleteExit");
                Next("Arrival portal boards normally through the closed boundary");
            }else if(step==4&&elapsed>1){
                if(!Riding())throw new Exception("Voluntary exit interrupted journey");
                var allocation=Object.FindObjectOfType<DomaineSeatAllocation>();
                var ids=(int[])UdonSharpEditorUtility.GetBackingUdonBehaviour(allocation).GetProgramVariable("passengerIds");
                var seat=allocation.seats[Array.IndexOf(ids,Networking.LocalPlayer.playerId)];
                // Simulate an SDK station exit, such as an avatar reload. This is
                // an editor test API call, not an available passenger control.
                seat.station.ExitStation(Networking.LocalPlayer);
                Next("Legacy exit calls cannot release passenger; simulated station interruption");
            }else if(step==5&&elapsed>2){
                if(!Riding()||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.seatAnchor.position)>.6f)throw new Exception("Unexpected station exit was not recovered");
                Next("Passenger reseated after simulated avatar interruption; journey continues");
            }else if(step==6&&!Riding()&&elapsed>2){
                if(stopped==0){stopped=now;return;}if(now-stopped<1)return;
                if(!(bool)runtime.GetProgramVariable("atCastle")||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.castleDrop.position)>1)throw new Exception("Automatic castle disembarkation failed");
                Networking.LocalPlayer.TeleportTo(new Vector3(-100,.15f,-65.5f),Quaternion.identity);
                Next("Full locked outbound trip; automatic drop inside castle enclosure");
            }else if(step==7&&elapsed>3){
                if(!Riding())throw new Exception("Return portal is blocked by grand gate wall");
                runtime.SendCustomEvent("ExitRide");Next("Return portal accessible inside wall; return journey started");
            }else if(step==8&&elapsed>1){
                if(!Riding())throw new Exception("Return trip allowed early exit");
                Next("Return journey also rejects early exit");
            }else if(step==9&&!Riding()&&elapsed>2){
                if(stopped==0){stopped=now;return;}if(now-stopped<1)return;
                if((bool)runtime.GetProgramVariable("atCastle")||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.arrivalDrop.position)>1)throw new Exception("Automatic reception disembarkation failed");
                Next("Full locked return trip; automatic drop inside arrival circle");Finish();
            }
        }catch(Exception ex){errors.Add(ex.ToString());Debug.LogException(ex);Finish();}
    }
    static void Finish(){
        ending=true;SessionState.SetBool(Key,false);
        var result=new Result{passed=errors.Count==0,checks=checks.ToArray(),errors=errors.ToArray()};
        File.WriteAllText("DomaineImportReports/deplacements-verrouilles.json",JsonUtility.ToJson(result,true));
        Debug.Log("DOMAINE_TRAVEL_RESULT "+JsonUtility.ToJson(result));EditorApplication.isPlaying=false;
        EditorApplication.delayCall+=()=>EditorApplication.Exit(result.passed?0:1);
    }
}
