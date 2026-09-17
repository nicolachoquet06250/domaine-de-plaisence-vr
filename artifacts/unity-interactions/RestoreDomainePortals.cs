using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using Object=UnityEngine.Object;

public static class RestoreDomainePortals
{
    const string Root=SetupDomaineInteractions.Root;
    public static void Run()
    {
        try {
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            string path=Root+"/Scripts/DomaineCoachPortal.asset";
            if(!AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(path)) {
                var program=ScriptableObject.CreateInstance<UdonSharpProgramAsset>();
                program.sourceCsScript=AssetDatabase.LoadAssetAtPath<MonoScript>(Root+"/Scripts/DomaineCoachPortal.cs");
                AssetDatabase.CreateAsset(program,path);
            }
            AssetDatabase.SaveAssets();AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
            var compiled=AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(path);
            if(compiled.SerializedProgramAsset.RetrieveProgram()==null)throw new Exception("Portal Udon compilation failed");
            var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            var coach=Object.FindObjectOfType<DomaineLocalCoach>();
            var source=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/DomainePlaisance/Models/scene-complete.fbx");
            var shader=Shader.Find("Domaine/Voile du portail");
            if(!shader||ShaderUtil.ShaderHasError(shader))throw new Exception("Portal veil shader failed");
            string matPath=Root+"/Materials/Voile du portail.mat";
            var veil=AssetDatabase.LoadAssetAtPath<Material>(matPath);
            if(!veil){veil=new Material(shader);AssetDatabase.CreateAsset(veil,matPath);}
            veil.shader=shader;var color=(Color)new Color32(0x70,0xc6,0xca,255);color.a=.21f;veil.SetColor("_Color",color);
            for(int i=0;i<2;i++) {
                string name=i==0?"Depart royal":"Retour royal";
                var old=GameObject.Find(name);Transform parent=old.transform.parent;
                // Only replace the two authored boarding panels and their labels.
                Object.DestroyImmediate(old);
                var portal=new GameObject(name);portal.transform.SetParent(parent,false);
                portal.transform.position=i==0?new Vector3(-7.15f,0,0):new Vector3(-100,0,-65.5f);
                portal.transform.rotation=Quaternion.Euler(0,i==0?-90:0,0);
                var original=source.GetComponentsInChildren<Transform>(true).Single(t=>t.name==(i==0?"coach-departure":"coach-return"));
                var visual=Object.Instantiate(original.gameObject);visual.name="Portail original - anneau or et voile turquoise";
                visual.transform.SetPositionAndRotation(original.position,original.rotation);visual.transform.localScale=original.lossyScale;
                visual.transform.SetParent(portal.transform,true);
                var renderers=visual.GetComponentsInChildren<MeshRenderer>();
                if(renderers.Length!=4)throw new Exception("Expected original ring, veil and two feet");
                int veils=0;
                foreach(var renderer in renderers) {
                    var mats=renderer.sharedMaterials;
                    for(int m=0;m<mats.Length;m++)if(mats[m].HasProperty("_Color")&&mats[m].GetColor("_Color").a<.5f){mats[m]=veil;veils++;}
                    renderer.sharedMaterials=mats;
                }
                if(veils!=1)throw new Exception("Original translucent portal surface not found");
                var bounds=renderers[0].bounds;foreach(var r in renderers)bounds.Encapsulate(r.bounds);
                if(Vector2.Distance(new Vector2(bounds.center.x,bounds.center.z),new Vector2(portal.transform.position.x,portal.transform.position.z))>.05f||bounds.size.y<2.2f||bounds.size.y>2.4f)
                    throw new Exception("Portal FBX placement or scale is incorrect: "+bounds);
                var trigger=portal.AddComponent<BoxCollider>();trigger.isTrigger=true;trigger.center=new Vector3(0,1.17f,0);trigger.size=new Vector3(1.65f,2.34f,1.2f);
                var behaviour=portal.AddUdonSharpComponent<DomaineCoachPortal>();behaviour.coach=coach;behaviour.destination=i;behaviour.visual=visual;behaviour.passage=trigger;
                var udon=UdonSharpEditorUtility.GetBackingUdonBehaviour(behaviour);udon.interactText="Entrer dans le carrosse";udon.proximity=2.5f;
                UdonSharpEditorUtility.CopyProxyToUdon(behaviour);
                if(portal.GetComponentsInChildren<TextMesh>(true).Length!=0||portal.GetComponentsInChildren<UnityEngine.UI.Text>(true).Length!=0)throw new Exception("Boarding text remains");
            }
            EditorUtility.SetDirty(veil);AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(scene);
            ValidateDomaineInteractions.Preview("portail-accueil.png",new Vector3(-3.4f,1.7f,3.3f),new Vector3(-7.15f,1.12f,0),52);
            ValidateDomaineInteractions.Preview("portail-retour.png",new Vector3(-96.7f,1.7f,-69.5f),new Vector3(-100,1.12f,-65.5f),52);
            ValidateDomainePortals.Run();
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
}
