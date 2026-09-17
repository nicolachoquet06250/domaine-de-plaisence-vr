using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using Object=UnityEngine.Object;

public static class ApplyDomaineTravelRules
{
    public const string BoundaryName="Limites invisibles de deplacement";
    public static void Run()
    {
        try {
            UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
            var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            var coach=Object.FindObjectOfType<DomaineLocalCoach>();
            foreach(var button in coach.GetComponentsInChildren<DomaineCoachButton>(true))
                if(button.action==2)Object.DestroyImmediate(button.gameObject);
            foreach(var seat in Object.FindObjectsOfType<DomainePassengerSeat>()) {
                seat.station.disableStationExit=true;
                seat.station.canUseStationFromStation=false;
                UdonSharpEditorUtility.CopyProxyToUdon(seat);
            }
            UdonSharpEditorUtility.CopyProxyToUdon(coach);
            var previous=GameObject.Find(BoundaryName);if(previous)Object.DestroyImmediate(previous);
            var root=new GameObject(BoundaryName);
            var circle=new GameObject("Cercle d'accueil - enceinte fermee");circle.transform.SetParent(root.transform,false);
            // Same 7.91 m radius as arrival-boundary.scene-asset.ts. Overlapping
            // tangent boxes prevent gaps, including behind the boarding portal.
            for(int i=0;i<96;i++) {
                float angle=i*Mathf.PI*2/96;
                Box(circle.transform,"Arc "+i,new Vector3(Mathf.Sin(angle)*7.91f,13,Mathf.Cos(angle)*7.91f),new Vector3(.57f,30,.45f),angle*Mathf.Rad2Deg);
            }
            var estate=new GameObject("Enceinte du chateau - portail et perimetre");estate.transform.SetParent(root.transform,false);
            // Authored enclosure spans x +/-30, z -40..30 around source (100,0,-95).
            // Unity reflects source X. The return portal stays 0.5 m inside the gate.
            Box(estate.transform,"Grand portail - fermeture invisible",new Vector3(-100,13,-65),new Vector3(60.6f,30,.4f));
            Box(estate.transform,"Mur du fond",new Vector3(-100,13,-135),new Vector3(60.6f,30,.6f));
            Box(estate.transform,"Cote ouest",new Vector3(-130,13,-100),new Vector3(.6f,30,70.6f));
            Box(estate.transform,"Cote est",new Vector3(-70,13,-100),new Vector3(.6f,30,70.6f));
            Physics.SyncTransforms();
            var colliders=root.GetComponentsInChildren<BoxCollider>();
            if(colliders.Length!=100||root.GetComponentsInChildren<Renderer>().Length!=0)throw new Exception("Invalid invisible walls");
            if(Physics.GetIgnoreLayerCollision(10,0))throw new Exception("PlayerLocal cannot collide with Default layer walls");
            // Sample between segment centres as well as at centres, at walk/jump height.
            foreach(float y in new[]{.3f,1.5f,4f,12f})for(int i=0;i<384;i++) {
                float a=i*Mathf.PI*2/384;Vector3 dir=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a));
                if(!colliders.Any(c=>c.Raycast(new Ray(new Vector3(0,y,0),dir),out RaycastHit hit,9)))throw new Exception("Gap in arrival perimeter");
            }
            foreach(float y in new[]{.3f,1.5f,4f,12f})for(int i=0;i<360;i++) {
                float a=i*Mathf.PI*2/360;Vector3 dir=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a));
                if(!estate.GetComponentsInChildren<BoxCollider>().Any(c=>c.Raycast(new Ray(new Vector3(-100,y,-100),dir),out RaycastHit hit,60)))throw new Exception("Gap in castle perimeter");
            }
            // Portal centres and destination drops must be inside, clear of the walls.
            foreach(var point in new[]{new Vector3(-7.15f,1,0),new Vector3(-100,1,-65.5f),coach.arrivalDrop.position+Vector3.up,coach.castleDrop.position+Vector3.up})
                if(colliders.Any(c=>Vector3.Distance(c.ClosestPoint(point),point)<.21f))throw new Exception("Barrier blocks portal or arrival drop");
            AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(scene);
            Debug.Log("DOMAINE_BOUNDARIES_CHECK 100 invisible colliders; 2976 perimeter rays passed; portal and drop clearance passed");
            ValidateDomaineTravelRules.Run();
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
    static void Box(Transform parent,string name,Vector3 center,Vector3 size,float yaw=0)
    {
        var go=new GameObject(name);go.transform.SetParent(parent,false);go.transform.position=center;go.transform.rotation=Quaternion.Euler(0,yaw,0);
        var collider=go.AddComponent<BoxCollider>();collider.size=size;collider.isTrigger=false;
    }
}
