using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using VRC.SDKBase;
using VRC.SDK3.ClientSim;
using Object=UnityEngine.Object;

[InitializeOnLoad]
public static class EnableDomaineJump
{
    const string Key="Domaine.JumpValidation";
    static double started,changed;
    static int step;
    static float ground,peak;
    static ClientSimPlayerController controller;
    static DomaineLocalCoach coach;
    [Serializable] public class Result {public bool passed;public float jumpImpulse,observedRise;public bool restoredAfterRespawn,passengerStayedSeated;public string error;}
    static EnableDomaineJump(){if(SessionState.GetBool(Key,false)){started=changed=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;}}
    public static void Run(){try{
        string root=SetupDomaineInteractions.Root,path=root+"/Scripts/DomaineJump.asset";
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        if(!AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(path)){
            var p=ScriptableObject.CreateInstance<UdonSharpProgramAsset>();p.sourceCsScript=AssetDatabase.LoadAssetAtPath<MonoScript>(root+"/Scripts/DomaineJump.cs");AssetDatabase.CreateAsset(p,path);
        }
        AssetDatabase.SaveAssets();UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
        if(AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(path).SerializedProgramAsset.RetrieveProgram()==null)throw new Exception("Jump Udon program missing");
        string backup="DomaineImportReports/scene-before-jump.unity.backup";if(!File.Exists(backup))File.Copy(SetupDomaineInteractions.ScenePath,backup);
        var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        var jump=Object.FindObjectOfType<DomaineJump>();
        if(!jump){var go=new GameObject("Saut des visiteurs");go.transform.SetParent(GameObject.Find("Interactions du Domaine").transform,false);jump=go.AddUdonSharpComponent<DomaineJump>();}
        jump.jumpImpulse=3.5f;UdonSharpEditorUtility.CopyProxyToUdon(jump);
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);if(!EditorSceneManager.SaveScene(scene))throw new Exception("Save failed");
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
        jump=Object.FindObjectOfType<DomaineJump>();float impulse;
        if(!UdonSharpEditorUtility.GetBackingUdonBehaviour(jump).publicVariables.TryGetVariableValue<float>("jumpImpulse",out impulse)||Mathf.Abs(impulse-3.5f)>.001f)throw new Exception("Jump value not serialized");
        SessionState.SetBool(Key,true);started=changed=EditorApplication.timeSinceStartup;EditorApplication.update-=Tick;EditorApplication.update+=Tick;EditorApplication.isPlaying=true;
    }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}}
    static void PressJump(){
        // Exercise the simulator's normal jump-input handler and physics movement.
        typeof(ClientSimPlayerController).GetField("_menuIsOpen",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(controller,false);
        var method=typeof(ClientSimPlayerController).GetMethod("JumpInput",BindingFlags.Instance|BindingFlags.NonPublic);
        method.Invoke(controller,new object[]{true,Enum.ToObject(method.GetParameters()[1].ParameterType,0)});
    }
    static void Next(){step++;changed=EditorApplication.timeSinceStartup;}
    static void Tick(){try{
        double now=EditorApplication.timeSinceStartup,elapsed=now-changed;
        if(now-started>80)throw new Exception("Jump test timeout at step "+step);
        if(!EditorApplication.isPlaying||!Utilities.IsValid(Networking.LocalPlayer))return;
        if(step==0&&elapsed>12){
            if(Mathf.Abs(Networking.LocalPlayer.GetJumpImpulse()-3.5f)>.001f)throw new Exception("Jump was not enabled on arrival");
            controller=Resources.FindObjectsOfTypeAll<ClientSimPlayerController>().Where(c=>c.gameObject.scene.IsValid()&&c.gameObject.activeInHierarchy).OrderBy(c=>Vector3.Distance(c.transform.position,Networking.LocalPlayer.GetPosition())).First();
            Networking.LocalPlayer.TeleportTo(new Vector3(0,.12f,2),Quaternion.identity);Next();
        }else if(step==1&&elapsed>1&&Networking.LocalPlayer.IsPlayerGrounded()){
            ground=Networking.LocalPlayer.GetPosition().y;peak=ground;PressJump();Next();
        }else if(step==2){
            peak=Mathf.Max(peak,Networking.LocalPlayer.GetPosition().y);
            if(elapsed<1.5)return;
            if(peak-ground<.25f)throw new Exception("Jump input did not lift player: "+(peak-ground));
            Networking.LocalPlayer.SetJumpImpulse(0);controller.Respawn();Next();
        }else if(step==3&&elapsed>1){
            if(Mathf.Abs(Networking.LocalPlayer.GetJumpImpulse()-3.5f)>.001f)throw new Exception("Jump not restored on respawn");
            coach=Object.FindObjectOfType<DomaineLocalCoach>();UdonSharpEditorUtility.GetBackingUdonBehaviour(coach).SendCustomEvent("BoardAtArrival");Next();
        }else if(step==4&&elapsed>2){
            if(!(bool)UdonSharpEditorUtility.GetBackingUdonBehaviour(coach).GetProgramVariable("riding"))throw new Exception("Coach boarding failed");
            PressJump();Next();
        }else if(step==5&&elapsed>1){
            if(!(bool)UdonSharpEditorUtility.GetBackingUdonBehaviour(coach).GetProgramVariable("riding")||Vector3.Distance(Networking.LocalPlayer.GetPosition(),coach.seatAnchor.position)>.6f)throw new Exception("Jump released passenger from carriage");
            if(Object.FindObjectsOfType<DomainePassengerSeat>().Any(s=>!s.station.disableStationExit))throw new Exception("Unlocked station");
            Finish(null);
        }
    }catch(Exception ex){Debug.LogException(ex);Finish(ex.ToString());}}
    static void Finish(string error){
        SessionState.SetBool(Key,false);EditorApplication.update-=Tick;
        var result=new Result{passed=error==null,jumpImpulse=Networking.LocalPlayer.GetJumpImpulse(),observedRise=peak-ground,restoredAfterRespawn=step>=4,passengerStayedSeated=error==null,error=error};
        File.WriteAllText("DomaineImportReports/saut-validation.json",JsonUtility.ToJson(result,true));Debug.Log("DOMAINE_JUMP "+JsonUtility.ToJson(result));EditorApplication.isPlaying=false;EditorApplication.delayCall+=()=>EditorApplication.Exit(error==null?0:1);
    }
}
