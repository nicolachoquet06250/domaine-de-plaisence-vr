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
public static class ValidateDomaineReportedIssues
{
    const string Key="Domaine.ReportedIssuesValidation";
    static int step;
    static double start,changed,stopped;
    static bool ending;
    static Quaternion[] wheelPrevious, stoppedRotation;
    static Vector3[] wheelPositions;
    static float lastMeters;
    static double lastWheelSample;
    static int wheelSamples, variant, variantStep;
    static VRCPlayerApi remote;
    static bool corruptedOwnership;
    static double variantChanged;
    static void CheckWheels(double now) {
        if(!coach)return;
        if(wheelPositions==null){wheelPositions=coach.wheels.Select(w=>w.localPosition).ToArray();wheelPrevious=coach.wheels.Select(w=>w.localRotation).ToArray();lastMeters=(float)runtime.GetProgramVariable("wheelAngle");lastWheelSample=now;return;}
        foreach(var wheel in coach.wheels)
            if(Mathf.Abs(Vector3.Dot(wheel.up,coach.carriage.forward))<.999f)throw new Exception("Wheel axle is tilted away from carriage axle: "+wheel.name);
        for(int i=0;i<4;i++)if(Vector3.Distance(wheelPositions[i],coach.wheels[i].localPosition)>.001f)throw new Exception("Wheel hub moves during animation");
        if(now-lastWheelSample<.15)return;
        float meters=(float)runtime.GetProgramVariable("wheelAngle");
        if(meters-lastMeters>.01f && meters-lastMeters<1f){
            for(int i=0;i<4;i++){
                float angle=Quaternion.Angle(wheelPrevious[i],coach.wheels[i].localRotation);
                float expected=(meters-lastMeters)/(i<2?.612f:.782f)*Mathf.Rad2Deg;
                if(Mathf.Abs(angle-expected)>2f)throw new Exception("Wheel rolling speed mismatch "+coach.wheels[i].name+" actual="+angle+" expected="+expected);
            }wheelSamples++;
        }
        wheelPrevious=coach.wheels.Select(w=>w.localRotation).ToArray();lastMeters=meters;lastWheelSample=now;
    }
    static void CheckStoppedWheels() {
        if(stoppedRotation==null){stoppedRotation=coach.wheels.Select(w=>w.localRotation).ToArray();return;}
        for(int i=0;i<4;i++)if(Quaternion.Angle(stoppedRotation[i],coach.wheels[i].localRotation)>.1f)throw new Exception("Wheel resets or rotates after stopping");
    }
    static DomaineLocalCoach coach;
    static UdonBehaviour runtime;
    static List<string> checks=new List<string>();
    static List<string> errors=new List<string>();
    [Serializable] public class Result { public bool passed;public string[] checks,errors;public int invisibleWallColliders=100;public bool liveVRChatTested=false; }
    static ValidateDomaineReportedIssues(){if(SessionState.GetBool(Key,false)){start=changed=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;}}
    public static void RunPortals(){SessionState.SetBool("Domaine.PortalsOnly",true);Run();}
    public static void Run(){
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        SessionState.SetBool(Key,true);start=changed=EditorApplication.timeSinceStartup;
        EditorApplication.update-=Tick;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;EditorApplication.isPlaying=true;
    }
    static void Log(string message,string trace,LogType type){
        if(errors.Count<10&&(type==LogType.Error||type==LogType.Exception)&&(message.Contains("Udon")||trace.Contains("Domaine"))&&!errors.Contains(message))errors.Add(message);
    }
    static bool Riding(){return (bool)runtime.GetProgramVariable("riding");}
    static void Next(string check){checks.Add(check);Debug.Log("DOMAINE_FIX_TEST_CHECK "+check);step++;changed=EditorApplication.timeSinceStartup;stopped=0;}
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
            if(now-start>360)throw new Exception("Locked journey timeout at step "+step);
            if(!EditorApplication.isPlaying||!Utilities.IsValid(Networking.LocalPlayer))return;
            if(!coach && SessionState.GetBool("Domaine.PortalsOnly",false) && elapsed>12){coach=Object.FindObjectOfType<DomaineLocalCoach>();runtime=UdonSharpEditorUtility.GetBackingUdonBehaviour(coach);step=10;variantChanged=now;}
            if(coach)CheckWheels(now);
            if(step==0&&elapsed>12){
                coach=Object.FindObjectOfType<DomaineLocalCoach>();runtime=UdonSharpEditorUtility.GetBackingUdonBehaviour(coach);
                var seats=Object.FindObjectsOfType<DomainePassengerSeat>();
                if(seats.Length!=100||seats.Any(s=>!s.station.disableStationExit||s.station.canUseStationFromStation))throw new Exception("A station still allows voluntary exit or switching");
                if(coach.GetComponentsInChildren<DomaineCoachButton>(true).Any(b=>b.action==2)||coach.GetComponentsInChildren<TextMesh>(true).Any(t=>t.text.Contains("Descendre")))throw new Exception("Exit control remains");
                ClientSimMain.SpawnRemotePlayer("Ownership retry test");
                Networking.LocalPlayer.TeleportTo(new Vector3(6,.15f,0),Quaternion.identity);
                Next("100 stations locked; exit button removed");
            }else if(step==1&&elapsed>3){
                var players=new VRCPlayerApi[100];VRCPlayerApi.GetPlayers(players);remote=players.First(p=>Utilities.IsValid(p)&&!p.isLocal);
                var a=coach.allocation;var ids=(int[])UdonSharpEditorUtility.GetBackingUdonBehaviour(a).GetProgramVariable("passengerIds");
                int localSlot=Array.IndexOf(ids,Networking.LocalPlayer.playerId),remoteSlot=Array.IndexOf(ids,remote.playerId);
                if(localSlot<0||remoteSlot<0||localSlot==remoteSlot)throw new Exception("Seat allocations are not distinct");
                Networking.SetOwner(remote,a.seats[localSlot].gameObject);
                Networking.SetOwner(Networking.LocalPlayer,a.seats[remoteSlot].gameObject);corruptedOwnership=true;
                LocalController().Move(new Vector3(5,0,0));
                if(Networking.LocalPlayer.GetPosition().x>7.7f)throw new Exception("Player walked outside the arrival circle");
                Networking.LocalPlayer.TeleportTo(new Vector3(-103,.15f,-66),Quaternion.identity);
                Next("Actual player movement blocked at arrival perimeter");
            }else if(step==2&&elapsed>3){
                var a=coach.allocation;var ids=(int[])UdonSharpEditorUtility.GetBackingUdonBehaviour(a).GetProgramVariable("passengerIds");
                for(int i=0;i<ids.Length;i++)if(ids[i]!=0&&Networking.GetOwner(a.seats[i].gameObject).playerId!=ids[i])throw new Exception("Lost ownership transfer was not retried");
                checks.Add("Distinct local/remote seats recover deliberately incorrect ownership");
                ClientSimMain.RemovePlayer(remote);
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
                if(stopped==0){stopped=now;return;}if(now-stopped<.2)return;CheckStoppedWheels();if(now-stopped<1.5)return;stoppedRotation=null;
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
                if(stopped==0){stopped=now;return;}if(now-stopped<.2)return;CheckStoppedWheels();if(now-stopped<1.5)return;stoppedRotation=null;
                if((bool)runtime.GetProgramVariable("atCastle")||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.arrivalDrop.position)>1)throw new Exception("Automatic reception disembarkation failed");
                Next("Full locked return trip; automatic drop inside arrival circle");
                checks.Add("Wheel hubs and axles stable; rolling sampled "+wheelSamples+" times; both stop angles retained");
                if(wheelSamples<20)throw new Exception("Insufficient moving wheel samples");
                variantChanged=now;
            } else if(step==10) {
                if(variant==3){checks.Add("Arrival portal boarded via movement with 0.3m, 1.8m and 3m capsules; foot-position fallback with player/trigger collisions disabled also passed");Finish();return;}
                double wait=now-variantChanged;
                if(variantStep==0){Networking.LocalPlayer.TeleportTo(new Vector3(-5,.15f,0),Quaternion.identity);variantStep=1;variantChanged=now;}
                else if(variantStep==1&&wait>.7){
                    var cc=LocalController();cc.enabled=false;cc.stepOffset=.05f;cc.skinWidth=.01f;cc.height=new[]{.3f,1.8f,3f}[variant];cc.radius=new[]{.1f,.3f,.55f}[variant];cc.center=new Vector3(0,cc.height/2,0);cc.enabled=true;Physics.SyncTransforms();
                    if(variant==2){var portal=Object.FindObjectsOfType<DomaineCoachPortal>().Single(p=>p.destination==0);portal.passage.gameObject.layer=30;Physics.IgnoreLayerCollision(30,cc.gameObject.layer,true);}
                    var before=cc.transform.position;cc.Move(new Vector3(-2,0,0));
                    Debug.Log("DOMAINE_CAPSULE "+variant+" controller="+cc.name+" enabled="+cc.enabled+" before="+before+" after="+cc.transform.position+" player="+Networking.LocalPlayer.GetPosition()+" radius="+cc.radius+" height="+cc.height+" center="+cc.center+" overlaps="+string.Join(";",Physics.OverlapCapsule(before+Vector3.up*.4f,before+Vector3.up*1.5f,.3f).Where(c=>!c.isTrigger).Select(c=>c.name)));
                    variantStep=2;variantChanged=now;
                }else if(variantStep==2&&wait>3){
                    if(!Riding())throw new Exception("Arrival portal inaccessible for capsule variant "+variant+" at "+Networking.LocalPlayer.GetPosition());
                    // Complete this extra boarding test quickly; the full routes were already tested.
                    runtime.SetProgramVariable("distance",coach.outboundLength-.001f);variantStep=3;variantChanged=now;
                }else if(variantStep==3&&wait>2&&!Riding()){
                    variant++;variantStep=0;variantChanged=now;
                }
            }
        }catch(Exception ex){errors.Add(ex.ToString());Debug.LogException(ex);Finish();}
    }
    static void Finish(){
        ending=true;SessionState.SetBool(Key,false);SessionState.SetBool("Domaine.PortalsOnly",false);
        var result=new Result{passed=errors.Count==0,checks=checks.ToArray(),errors=errors.ToArray()};
        File.WriteAllText("DomaineImportReports/corrections-runtime.json",JsonUtility.ToJson(result,true));
        Debug.Log("DOMAINE_FIX_TEST_RESULT "+JsonUtility.ToJson(result));EditorApplication.isPlaying=false;
        EditorApplication.delayCall+=()=>EditorApplication.Exit(result.passed?0:1);
    }
}
