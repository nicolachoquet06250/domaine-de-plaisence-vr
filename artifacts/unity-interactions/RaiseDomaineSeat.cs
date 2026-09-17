using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharpEditor;

public static class RaiseDomaineSeat
{
    [Serializable] public class Result { public float previousViewHeight,newViewHeight,anchorHeight;public bool saved,udonValueVerified; }
    public static void Run()
    {
        try {
            UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
            var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            var coach=UnityEngine.Object.FindObjectOfType<DomaineLocalCoach>();
            var result=new Result{previousViewHeight=coach.seatViewHeight,newViewHeight=2.48f};
            Vector3 p=coach.seatAnchor.localPosition;p.y+=2.48f-coach.seatViewHeight;
            coach.seatAnchor.localPosition=p;coach.seatViewHeight=2.48f;
            UdonSharpEditorUtility.CopyProxyToUdon(coach);
            result.anchorHeight=p.y;
            AssetDatabase.SaveAssets();result.saved=EditorSceneManager.SaveScene(scene);
            EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            coach=UnityEngine.Object.FindObjectOfType<DomaineLocalCoach>();
            var backing=UdonSharpEditorUtility.GetBackingUdonBehaviour(coach);
            float serializedHeight;
            result.udonValueVerified=backing.publicVariables.TryGetVariableValue<float>("seatViewHeight",out serializedHeight)&&Mathf.Abs(serializedHeight-2.48f)<.001f;
            if(!result.saved||!result.udonValueVerified)throw new Exception("Passenger height did not persist in Udon scene data");
            Vector3 eye=coach.carriage.TransformPoint(new Vector3(.6f,2.48f,0));
            ValidateDomaineInteractions.Preview("vue-passager-rehaussee.png",eye,eye+coach.carriage.TransformDirection(Vector3.left)*10f,80);
            File.WriteAllText("DomaineImportReports/hauteur-passager.json",JsonUtility.ToJson(result,true));
            Debug.Log("DOMAINE_SEAT_HEIGHT "+JsonUtility.ToJson(result));EditorApplication.Exit(0);
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
}
