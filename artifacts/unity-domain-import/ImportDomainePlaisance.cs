using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using VRC.SDK3.Components;

public static class ImportDomainePlaisance {
    const string Root="Assets/DomainePlaisance";
    const string Model=Root+"/Models/scene-complete.fbx";
    const string ScenePath=Root+"/Scenes/Domaine de Plaisance.unity";
    [Serializable] public class MaterialSpec {
        public string name,baseTexture,normalTexture,alphaTexture,emissionTexture;
        public float[] baseColor,emission;
        public float metallic,roughness,alpha,normalStrength,emissionStrength,cutoff;
        public bool doubleSided,masked;
    }
    [Serializable] public class Manifest { public MaterialSpec[] materials; }
    [Serializable] public class Result {
        public string unityVersion,scene,prefab;
        public int meshes,materials,textures,normalMaps,transparentMaterials,cutoutMaterials,colliders;
        public long triangles;
        public bool interiorSeparate,allMaterialsAssigned,allExpectedTexturesAssigned,sceneReloaded;
        public string[] previews;
    }
    static Color ColorFromLinear(float[] v,float alpha=1) {
        var c=new Color(v[0],v[1],v[2],alpha).gamma;c.a=alpha;return c;
    }
    static Texture2D Texture(string filename) {
        if(string.IsNullOrEmpty(filename))return null;
        var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Textures/"+filename);
        if(texture==null)throw new Exception("Missing texture: "+filename);
        return texture;
    }
    static string Safe(string text) {
        foreach(char c in Path.GetInvalidFileNameChars())text=text.Replace(c,'_');
        return text;
    }
    static void Preview(string filename,Vector3 position,Vector3 target,float fov) {
        var go=new GameObject("Camera de controle temporaire");
        var camera=go.AddComponent<Camera>();camera.transform.position=position;
        camera.transform.LookAt(target);camera.fieldOfView=fov;camera.nearClipPlane=.1f;camera.farClipPlane=700;
        camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.49f,.57f,.64f);
        var rt=new RenderTexture(1200,850,24);camera.targetTexture=rt;
        camera.Render();var previous=RenderTexture.active;RenderTexture.active=rt;
        var image=new Texture2D(1200,850,TextureFormat.RGB24,false);
        image.ReadPixels(new Rect(0,0,1200,850),0,0);image.Apply();
        File.WriteAllBytes("DomaineImportReports/"+filename,image.EncodeToPNG());
        RenderTexture.active=previous;camera.targetTexture=null;
        UnityEngine.Object.DestroyImmediate(image);rt.Release();UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(go);
    }
    public static void Run() {
        try {
            Directory.CreateDirectory("DomaineImportReports");
            var manifest=JsonUtility.FromJson<Manifest>(File.ReadAllText(Root+"/Source/materials-source.json"));
            Directory.CreateDirectory(Root+"/Materials");Directory.CreateDirectory(Root+"/Scenes");Directory.CreateDirectory(Root+"/Prefabs");
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            var normalNames=new HashSet<string>(manifest.materials.Where(m=>!string.IsNullOrEmpty(m.normalTexture)).Select(m=>m.normalTexture));
            foreach(string path in Directory.GetFiles(Root+"/Textures","*.png")) {
                var importer=(TextureImporter)AssetImporter.GetAtPath(path.Replace('\\','/'));
                bool normal=normalNames.Contains(Path.GetFileName(path));
                importer.textureType=normal?TextureImporterType.NormalMap:TextureImporterType.Default;
                importer.sRGBTexture=!normal;importer.alphaSource=TextureImporterAlphaSource.FromInput;
                importer.alphaIsTransparency=!normal;importer.mipmapEnabled=true;importer.maxTextureSize=2048;
                importer.SaveAndReimport();
            }
            var modelImporter=(ModelImporter)AssetImporter.GetAtPath(Model);
            modelImporter.importAnimation=false;modelImporter.isReadable=true;
            modelImporter.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
            modelImporter.SaveAndReimport();
            var specs=manifest.materials.ToDictionary(m=>m.name,StringComparer.Ordinal);
            var embedded=AssetDatabase.LoadAllAssetsAtPath(Model).OfType<Material>().ToArray();
            var created=new Dictionary<string,Material>();
            foreach(var src in embedded)if(!specs.ContainsKey(src.name))throw new Exception("No source material mapping for "+src.name);
            foreach(var spec in manifest.materials) {
                bool transparent=spec.alpha<.999f||(!spec.masked&&!string.IsNullOrEmpty(spec.alphaTexture));
                var shader=Shader.Find(transparent?"Domaine/PBR Transparent":"Domaine/PBR");
                if(shader==null)throw new Exception("Domaine shader missing");
                var mat=new Material(shader);mat.name=spec.name;mat.enableInstancing=true;
                mat.SetColor("_Color",ColorFromLinear(spec.baseColor,spec.alpha));
                mat.SetTexture("_MainTex",Texture(spec.baseTexture));
                mat.SetFloat("_Metallic",spec.metallic);mat.SetFloat("_Glossiness",1-spec.roughness);
                mat.SetFloat("_Cull",spec.doubleSided?0:2);
                if(!string.IsNullOrEmpty(spec.normalTexture)) {
                    mat.SetTexture("_BumpMap",Texture(spec.normalTexture));mat.SetFloat("_BumpScale",spec.normalStrength);
                }
                var emission=ColorFromLinear(spec.emission)*spec.emissionStrength;
                mat.SetColor("_EmissionColor",emission);mat.SetTexture("_EmissionMap",Texture(spec.emissionTexture));
                if(spec.emissionStrength>0)mat.globalIlluminationFlags=MaterialGlobalIlluminationFlags.RealtimeEmissive;
                if(spec.masked) {
                    mat.SetFloat("_AlphaClip",1);mat.SetFloat("_Cutoff",spec.cutoff);
                    mat.SetOverrideTag("RenderType","TransparentCutout");mat.renderQueue=(int)RenderQueue.AlphaTest;
                }
                string materialPath=Root+"/Materials/"+Safe(spec.name)+".mat";
                var existing=AssetDatabase.LoadAssetAtPath<Material>(materialPath);
                if(existing!=null){EditorUtility.CopySerialized(mat,existing);UnityEngine.Object.DestroyImmediate(mat);mat=existing;}
                else AssetDatabase.CreateAsset(mat,materialPath);
                modelImporter.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material),spec.name),mat);
                created.Add(spec.name,mat);
            }
            if(created.Count!=manifest.materials.Length)throw new Exception("Material count mismatch: "+created.Count+" / "+manifest.materials.Length);
            AssetDatabase.SaveAssets();modelImporter.SaveAndReimport();
            var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var model=AssetDatabase.LoadAssetAtPath<GameObject>(Model);
            var instance=(GameObject)PrefabUtility.InstantiatePrefab(model);instance.name="Domaine de Plaisance";
            // Static walkable geometry and architectural boundaries, excluding decorative water/portals.
            foreach(var filter in instance.GetComponentsInChildren<MeshFilter>(true)) {
                var parent=filter.transform.parent;
                string group=parent?parent.name:"";
                bool solid=filter.name=="Interieur_Chateau"||group=="castle__palace"||group.StartsWith("castle__door-")||
                    group=="arrival-terrace"||group=="landscape-terrain"||group=="landscape-path"||
                    group=="gardens__ground"||group.StartsWith("gardens__allee-")||group=="gardens__terrasse"||group=="gardens__entree"||
                    group=="royal-enclosure__gate"||group=="royal-enclosure__fence"||group=="royal-enclosure__approach";
                if(solid)filter.gameObject.AddComponent<MeshCollider>().sharedMesh=filter.sharedMesh;
            }
            foreach(var light in instance.GetComponentsInChildren<Light>(true)) {
                if(light.type==LightType.Directional){light.intensity=1.3f;light.shadows=LightShadows.Soft;RenderSettings.sun=light;}
                else {light.intensity=1.2f;light.range=10;light.shadows=LightShadows.None;}
            }
            RenderSettings.ambientMode=AmbientMode.Trilight;
            RenderSettings.ambientSkyColor=new Color(.5f,.58f,.68f);
            RenderSettings.ambientEquatorColor=new Color(.38f,.38f,.33f);
            RenderSettings.ambientGroundColor=new Color(.20f,.24f,.16f);
            var world=new GameObject("VRCWorld").AddComponent<VRCSceneDescriptor>();
            var spawn=new GameObject("Arrivee visiteurs").transform;spawn.position=new Vector3(0,.12f,2);
            spawn.rotation=Quaternion.Euler(0,180,0);world.spawns=new[]{spawn};world.RespawnHeightY=-15;
            string prefabPath=Root+"/Prefabs/Domaine de Plaisance.prefab";
            PrefabUtility.SaveAsPrefabAsset(instance,prefabPath);
            if(!EditorSceneManager.SaveScene(scene,ScenePath))throw new Exception("Scene save failed");
            EditorSceneManager.OpenScene(ScenePath,OpenSceneMode.Single);
            var filters=UnityEngine.Object.FindObjectsOfType<MeshFilter>();
            var renderers=UnityEngine.Object.FindObjectsOfType<MeshRenderer>();
            bool assigned=renderers.All(r=>r.sharedMaterials.Length>0&&r.sharedMaterials.All(m=>m!=null&&AssetDatabase.GetAssetPath(m).StartsWith(Root+"/Materials/")));
            bool texturesOk=created.All(pair=> {
                var spec=specs[pair.Key];var mat=pair.Value;
                return (string.IsNullOrEmpty(spec.baseTexture)||mat.GetTexture("_MainTex")!=null)&&
                    (string.IsNullOrEmpty(spec.normalTexture)||mat.GetTexture("_BumpMap")!=null)&&
                    (string.IsNullOrEmpty(spec.emissionTexture)||mat.GetTexture("_EmissionMap")!=null);
            });
            foreach(var shader in created.Values.Select(m=>m.shader).Distinct())
                if(ShaderUtil.ShaderHasError(shader))throw new Exception("Shader errors: "+shader.name);
            Preview("vue-ensemble-unity.png",new Vector3(-175,130,95),new Vector3(-50,0,-55),57);
            Preview("chateau-unity.png",new Vector3(-145,30,-66),new Vector3(-100,5,-117),57);
            Preview("interieur-unity.png",new Vector3(-100,2.2f,-118),new Vector3(-100,3.4f,-127),80);
            foreach(var shader in created.Values.Select(m=>m.shader).Distinct())
                if(ShaderUtil.ShaderHasError(shader))throw new Exception("Shader compilation failed during preview: "+shader.name);
            var result=new Result {unityVersion=Application.unityVersion,scene=ScenePath,prefab=prefabPath,
                meshes=filters.Length,materials=created.Count,textures=Directory.GetFiles(Root+"/Textures","*.png").Length,
                normalMaps=normalNames.Count,transparentMaterials=created.Values.Count(m=>m.renderQueue>=3000),
                cutoutMaterials=created.Values.Count(m=>m.renderQueue==2450),colliders=UnityEngine.Object.FindObjectsOfType<MeshCollider>().Length,
                triangles=filters.Sum(m=>(long)m.sharedMesh.triangles.Length/3),interiorSeparate=filters.Count(m=>m.name=="Interieur_Chateau")==1,
                allMaterialsAssigned=assigned,allExpectedTexturesAssigned=texturesOk,sceneReloaded=true,
                previews=new[]{"vue-ensemble-unity.png","chateau-unity.png","interieur-unity.png"}};
            File.WriteAllText("DomaineImportReports/import-result.json",JsonUtility.ToJson(result,true));
            AssetDatabase.SaveAssets();
            Debug.Log("DOMAINE_IMPORT_RESULT "+JsonUtility.ToJson(result));
            if(filters.Length!=154||!assigned||!texturesOk||!result.interiorSeparate)throw new Exception("Scene verification failed");
            EditorApplication.Exit(0);
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
}
