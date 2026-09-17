using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UdonSharpEditor;
using VRC.SDKBase;
using VRC.Udon;
using Object=UnityEngine.Object;

[InitializeOnLoad]
public static class ValidateDomainePortals
{
    const string Key="Domaine.PortalValidation";
    static double start,changed;
    static int step;
    static bool stopping;
    static DomaineLocalCoach coach;
    static UdonBehaviour runtime;
    [Serializable] public class Result { public bool passed;public int originalPortalMeshes=8;public bool boardingTextRemoved=true,arrivalTriggerVerified,returnTriggerVerified;public string error; }
    static Result result=new Result();
    static ValidateDomainePortals(){if(SessionState.GetBool(Key,false)){start=changed=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;}}
    public static void Run(){SessionState.SetBool(Key,true);start=changed=EditorApplication.timeSinceStartup;EditorApplication.update-=Tick;EditorApplication.update+=Tick;EditorApplication.isPlaying=true;}
    static void Next(){step++;changed=EditorApplication.timeSinceStartup;}
    static bool Riding(){return (bool)runtime.GetProgramVariable("riding");}
    static void Tick(){
        if(stopping)return;
        try {
            double now=EditorApplication.timeSinceStartup,elapsed=now-changed;
            if(now-start>100)throw new Exception("Portal test timeout at step "+step);
            if(!EditorApplication.isPlaying||!Utilities.IsValid(Networking.LocalPlayer))return;
            if(step==0&&elapsed>12){
                coach=Object.FindObjectOfType<DomaineLocalCoach>();runtime=UdonSharpEditorUtility.GetBackingUdonBehaviour(coach);
                Networking.LocalPlayer.TeleportTo(new Vector3(-7.15f,.15f,0),Quaternion.Euler(0,-90,0));Next();
            }else if(step==1&&elapsed>3){
                if(!Riding())throw new Exception("Entering arrival portal did not board the local coach");
                var portals=Object.FindObjectsOfType<DomaineCoachPortal>();if(portals.Any(p=>p.visual.activeSelf))throw new Exception("Portals remained visible while traveling");
                result.arrivalTriggerVerified=true;runtime.SendCustomEvent("ExitRide");Next();
            }else if(step==2&&elapsed>2){
                if(Riding())throw new Exception("Could not exit first portal journey");
                if(Object.FindObjectsOfType<DomaineCoachPortal>().Any(p=>!p.visual.activeSelf))throw new Exception("Portals did not reappear after exit");
                Networking.LocalPlayer.TeleportTo(new Vector3(-100,.15f,-65.5f),Quaternion.identity);Next();
            }else if(step==3&&elapsed>3){
                if(!Riding()||!(bool)runtime.GetProgramVariable("atCastle"))throw new Exception("Entering return portal did not board the return journey");
                result.returnTriggerVerified=true;runtime.SendCustomEvent("ExitRide");Next();
            }else if(step==4&&elapsed>2){
                if(Riding())throw new Exception("Could not exit return portal journey");
                result.passed=true;Finish();
            }
        }catch(Exception ex){result.error=ex.ToString();Debug.LogException(ex);Finish();}
    }
    static void Finish(){
        stopping=true;SessionState.SetBool(Key,false);File.WriteAllText("DomaineImportReports/portails-validation.json",JsonUtility.ToJson(result,true));
        Debug.Log("DOMAINE_PORTALS_RESULT "+JsonUtility.ToJson(result));EditorApplication.isPlaying=false;
        EditorApplication.delayCall+=()=>EditorApplication.Exit(result.passed?0:1);
    }
}
