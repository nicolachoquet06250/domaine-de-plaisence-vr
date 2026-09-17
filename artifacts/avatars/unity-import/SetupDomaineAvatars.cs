using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using VRC.SDK3.Avatars.Components;
using VRC.SDKBase;

// Editor-only, bounded to Assets/DomaineAvatars. Never uploads to VRChat.
[InitializeOnLoad]
public static class SetupDomaineAvatars
{
    const string Root = "Assets/DomaineAvatars";
    const string ReportPath = "Logs/domaine-avatars-import.json";
    const string Pending = "ProjectSettings/DomaineAvatarsImport.pending";
    static readonly string[] Names = { "courtMale", "courtFemale" };
    static readonly string[] Visemes = { "sil", "PP", "FF", "TH", "DD", "kk", "CH", "SS", "nn", "RR", "aa", "E", "I", "O", "U" };
    [Serializable] public class MaterialSpec { public string name; public float metallic; public float roughness; public string[] textures; }
    [Serializable] public class MaterialSpecs { public MaterialSpec[] materials; }
    [Serializable] public class AvatarResult {
        public string name, prefab, face, lipSync;
        public bool humanoid, valid, allVisemesDeform, shouldersMapped;
        public int triangles, renderers, materials;
        public Vector3 viewpoint;
        public string[] visemes, clips;
    }
    [Serializable] public class Report { public bool success; public string error; public AvatarResult[] avatars; }
    static SetupDomaineAvatars() {
        if (!Application.isBatchMode && File.Exists(Pending)) EditorApplication.delayCall += AutoRun;
    }
    static void AutoRun() {
        if (!File.Exists(Pending)) return;
        if (EditorApplication.isCompiling || EditorApplication.isUpdating) { EditorApplication.delayCall += AutoRun; return; }
        File.Delete(Pending);
        Run();
    }
    [MenuItem("Domaine/Importer et configurer les avatars Renaissance")]
    public static void Run() {
        var report = new Report();
        var results = new List<AvatarResult>();
        Scene preview = default(Scene);
        try {
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            foreach (var name in Names) results.Add(Configure(name));
            report.avatars = results.ToArray();
            preview = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, Application.isBatchMode ? NewSceneMode.Single : NewSceneMode.Additive);
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.65f, 0.65f, 0.65f);
            for (int i = 0; i < Names.Length; i++) {
                var instance = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Root + "/" + Names[i] + "/" + Names[i] + "-VRChat.prefab"), preview);
                instance.transform.position = new Vector3((i - 0.5f) * 1.0f, 0, 0);
            }
            var lightObject = new GameObject("Preview light", typeof(Light));
            SceneManager.MoveGameObjectToScene(lightObject, preview);
            lightObject.GetComponent<Light>().type = LightType.Directional;
            lightObject.GetComponent<Light>().intensity = 1.1f;
            lightObject.transform.rotation = Quaternion.Euler(25, 155, 0);
            var cameraObject = new GameObject("Preview camera", typeof(Camera));
            SceneManager.MoveGameObjectToScene(cameraObject, preview);
            var camera = cameraObject.GetComponent<Camera>();
            cameraObject.transform.position = new Vector3(0, 1.05f, 3.7f);
            cameraObject.transform.LookAt(new Vector3(0, 0.92f, 0));
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.16f, 0.18f, 0.22f);
            camera.fieldOfView = 35;
            var scenePath = Root + "/Avatars-Renaissance.unity";
            EditorSceneManager.SaveScene(preview, scenePath);
            var target = new RenderTexture(1200, 1000, 24);
            var previous = RenderTexture.active;
            var texture = new Texture2D(1200, 1000, TextureFormat.RGB24, false);
            try {
                camera.targetTexture = target;
                camera.Render();
                RenderTexture.active = target;
                texture.ReadPixels(new Rect(0, 0, 1200, 1000), 0, 0);
                texture.Apply();
                File.WriteAllBytes("Logs/domaine-avatars-preview.png", texture.EncodeToPNG());
            } finally {
                camera.targetTexture = null;
                RenderTexture.active = previous;
                UnityEngine.Object.DestroyImmediate(texture);
                target.Release();
                UnityEngine.Object.DestroyImmediate(target);
            }
            AssetDatabase.SaveAssets();
            report.success = results.All(r => r.humanoid && r.valid && r.shouldersMapped && r.allVisemesDeform && r.visemes.Length == 15);
            if (File.Exists(Pending)) File.Delete(Pending);
        } catch (Exception e) { report.error = e.ToString(); Debug.LogException(e); }
        finally {
            report.avatars = results.ToArray();
            Directory.CreateDirectory("Logs");
            File.WriteAllText(ReportPath, JsonUtility.ToJson(report, true));
            if (preview.IsValid()) EditorSceneManager.CloseScene(preview, true);
        }
        Debug.Log("DOMAINE_AVATARS_IMPORT " + JsonUtility.ToJson(report));
        if (Application.isBatchMode) EditorApplication.Exit(report.success ? 0 : 1);
    }
    static AvatarResult Configure(string name) {
        string folder = Root + "/" + name;
        string path = folder + "/" + name + ".fbx";
        var specs = JsonUtility.FromJson<MaterialSpecs>(File.ReadAllText(folder + "/materials-source.json"));
        foreach (string texturePath in Directory.GetFiles(folder + "/Textures", "*.png")) {
            var textureImporter = (TextureImporter)AssetImporter.GetAtPath(texturePath.Replace('\\', '/'));
            textureImporter.textureType = texturePath.Contains("-normal") ? TextureImporterType.NormalMap : TextureImporterType.Default;
            textureImporter.mipmapEnabled = true;
            textureImporter.streamingMipmaps = true;
            textureImporter.SaveAndReimport();
        }
        var importer = (ModelImporter)AssetImporter.GetAtPath(path);
        importer.importBlendShapes = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.importAnimation = true;
        importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
        // First obtain Unity's imported bind-pose skeleton, then map its named bones.
        importer.animationType = ModelImporterAnimationType.Generic;
        importer.SaveAndReimport();
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        var skeleton = model.GetComponentsInChildren<Transform>(true);
        var mapping = new Dictionary<string, string> {
            {"Hips", "Hips"}, {"Spine", "Spine"}, {"Chest", "Chest"}, {"Neck", "Neck"}, {"Head", "Head"},
            {"LeftUpperArm", "UpperArm.L"}, {"LeftLowerArm", "Forearm.L"}, {"LeftHand", "Hand.L"},
            {"RightUpperArm", "UpperArm.R"}, {"RightLowerArm", "Forearm.R"}, {"RightHand", "Hand.R"},
            {"LeftUpperLeg", "Thigh.L"}, {"LeftLowerLeg", "Shin.L"}, {"LeftFoot", "Foot.L"},
            {"RightUpperLeg", "Thigh.R"}, {"RightLowerLeg", "Shin.R"}, {"RightFoot", "Foot.R"}
        };
        foreach (string bone in mapping.Values) if (!skeleton.Any(t => t.name == bone)) throw new Exception(name + ": missing bone " + bone);
        var human = importer.humanDescription;
        human.human = mapping.Select(p => new HumanBone { humanName = p.Key, boneName = p.Value, limit = new HumanLimit { useDefaultValues = true } }).ToArray();
        human.skeleton = skeleton.Select(t => new SkeletonBone { name = t.name, position = t.localPosition, rotation = t.localRotation, scale = t.localScale }).ToArray();
        human.upperArmTwist = human.lowerArmTwist = human.upperLegTwist = human.lowerLegTwist = 0.5f;
        human.armStretch = human.legStretch = 0.05f;
        human.feetSpacing = 0;
        human.hasTranslationDoF = false;
        importer.animationType = ModelImporterAnimationType.Human;
        importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
        importer.humanDescription = human;
        importer.SaveAndReimport();
        model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        string materialFolder = folder + "/Materials";
        if (!AssetDatabase.IsValidFolder(materialFolder)) AssetDatabase.CreateFolder(folder, "Materials");
        foreach (var source in model.GetComponentsInChildren<Renderer>(true).SelectMany(r => r.sharedMaterials).Where(m => m != null).Distinct()) {
            var spec = specs.materials.FirstOrDefault(m => m.name == source.name);
            if (spec == null) throw new Exception("Unknown material: " + source.name);
            string safeName = string.Concat(source.name.Select(c => Path.GetInvalidFileNameChars().Contains(c) ? '_' : c));
            string materialPath = materialFolder + "/" + safeName + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (material == null) { material = new Material(source); AssetDatabase.CreateAsset(material, materialPath); }
            material.shader = Shader.Find("Standard");
            material.SetFloat("_Metallic", spec.metallic);
            material.SetFloat("_Glossiness", 1 - spec.roughness);
            foreach (var relative in spec.textures) {
                var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(folder + "/" + relative);
                if (texture == null) throw new Exception("Missing texture: " + relative);
                if (relative.Contains("-normal")) { material.SetTexture("_BumpMap", texture); material.EnableKeyword("_NORMALMAP"); }
                else { material.mainTexture = texture; material.color = Color.white; }
            }
            EditorUtility.SetDirty(material);
            importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), source.name), material);
        }
        importer.SaveAndReimport();
        model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(model);
        try {
            PrefabUtility.UnpackPrefabInstance(instance, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            instance.name = name + "-VRChat";
            var animator = instance.GetComponent<Animator>();
            if (animator == null || animator.avatar == null || !animator.avatar.isValid || !animator.avatar.isHuman) throw new Exception(name + ": invalid humanoid avatar");
            AddShouldersAndTPose(instance, mapping, human, folder, animator);
            animator = instance.GetComponent<Animator>();
            var renderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            var face = renderers.Single(r => r.sharedMesh.blendShapeCount >= 15);
            var shapeNames = Enumerable.Range(0, face.sharedMesh.blendShapeCount).Select(face.sharedMesh.GetBlendShapeName).ToArray();
            var descriptor = instance.GetComponent<VRCAvatarDescriptor>() ?? instance.AddComponent<VRCAvatarDescriptor>();
            descriptor.lipSync = VRC_AvatarDescriptor.LipSyncStyle.VisemeBlendShape;
            descriptor.VisemeSkinnedMesh = face;
            descriptor.VisemeBlendShapes = Visemes.Select(v => shapeNames.Single(s => s == "viseme_" + v || s.EndsWith(".viseme_" + v, StringComparison.Ordinal))).ToArray();
            descriptor.customizeAnimationLayers = false;
            descriptor.baseAnimationLayers = new[] { VRCAvatarDescriptor.AnimLayerType.Base, VRCAvatarDescriptor.AnimLayerType.Additive, VRCAvatarDescriptor.AnimLayerType.Gesture, VRCAvatarDescriptor.AnimLayerType.Action, VRCAvatarDescriptor.AnimLayerType.FX }.Select(t => new VRCAvatarDescriptor.CustomAnimLayer { type = t, isDefault = true }).ToArray();
            descriptor.specialAnimationLayers = new[] { VRCAvatarDescriptor.AnimLayerType.Sitting, VRCAvatarDescriptor.AnimLayerType.TPose, VRCAvatarDescriptor.AnimLayerType.IKPose }.Select(t => new VRCAvatarDescriptor.CustomAnimLayer { type = t, isDefault = true }).ToArray();
            // Eye meshes are authored independently; center the view between their bounds.
            var eyes = renderers.Where(r => r.name.IndexOf("yeux", StringComparison.OrdinalIgnoreCase) >= 0 || r.name.IndexOf("oeil", StringComparison.OrdinalIgnoreCase) >= 0 || r.name.IndexOf("iris", StringComparison.OrdinalIgnoreCase) >= 0).ToArray();
            Vector3 eyePosition = eyes.Length > 0 ? eyes.Aggregate(Vector3.zero, (a, r) => a + r.bounds.center) / eyes.Length : animator.GetBoneTransform(HumanBodyBones.Head).position + new Vector3(0, 0.06f, 0.10f);
            descriptor.ViewPosition = instance.transform.InverseTransformPoint(eyePosition);
            if (instance.GetComponent<VRC.Core.PipelineManager>() == null) instance.AddComponent<VRC.Core.PipelineManager>();
            var delta = new Vector3[face.sharedMesh.vertexCount];
            bool deforms = true;
            foreach (string shape in descriptor.VisemeBlendShapes) {
                int index = face.sharedMesh.GetBlendShapeIndex(shape);
                face.sharedMesh.GetBlendShapeFrameVertices(index, face.sharedMesh.GetBlendShapeFrameCount(index) - 1, delta, null, null);
                deforms &= delta.Any(d => d.sqrMagnitude > 1e-12f);
                face.SetBlendShapeWeight(index, 0);
            }
            string prefabPath = folder + "/" + name + "-VRChat.prefab";
            PrefabUtility.SaveAsPrefabAsset(instance, prefabPath, out bool saved);
            if (!saved) throw new Exception("Prefab save failed: " + prefabPath);
            var persisted = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath).GetComponent<VRCAvatarDescriptor>();
            if (persisted.VisemeSkinnedMesh == null || !persisted.VisemeBlendShapes.SequenceEqual(descriptor.VisemeBlendShapes)) throw new Exception("Viseme prefab serialization failed");
            return new AvatarResult {
                name = name, prefab = prefabPath, humanoid = animator.avatar.isHuman, valid = animator.avatar.isValid,
                shouldersMapped = animator.GetBoneTransform(HumanBodyBones.LeftShoulder) != null && animator.GetBoneTransform(HumanBodyBones.RightShoulder) != null,
                face = face.name, lipSync = descriptor.lipSync.ToString(), visemes = descriptor.VisemeBlendShapes,
                viewpoint = descriptor.ViewPosition, allVisemesDeform = deforms,
                renderers = renderers.Length, triangles = renderers.Sum(r => r.sharedMesh.triangles.Length / 3),
                materials = renderers.SelectMany(r => r.sharedMaterials).Distinct().Count(),
                clips = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).Select(c => c.name).ToArray()
            };
        } finally { UnityEngine.Object.DestroyImmediate(instance); }
    }
    static void AddShouldersAndTPose(GameObject instance, Dictionary<string, string> mapping, HumanDescription human, string folder, Animator animator) {
        // An Animator carrying the FBX avatar restores the old local bone positions on cloning.
        // Remove it while changing hierarchy so the shoulders cannot offset the bind pose twice.
        UnityEngine.Object.DestroyImmediate(animator);
        var bones = instance.GetComponentsInChildren<Transform>(true).ToDictionary(t => t.name);
        foreach (var side in new[] { "L", "R" }) {
            var arm = bones["UpperArm." + side];
            var shoulder = new GameObject("Shoulder." + side).transform;
            shoulder.SetParent(bones["Chest"], false);
            shoulder.position = new Vector3(arm.position.x * 0.35f, arm.position.y, arm.position.z);
            arm.SetParent(shoulder, true);
            mapping.Add(side == "L" ? "LeftShoulder" : "RightShoulder", shoulder.name);
        }
        // Build the human reference pose on a temporary clone; keep the mesh bind pose intact.
        var posed = UnityEngine.Object.Instantiate(instance);
        try {
            posed.name = instance.name;
            var transforms = posed.GetComponentsInChildren<Transform>(true);
            var b = transforms.ToDictionary(t => t.name);
            foreach (var side in new[] { "L", "R" }) {
                var upper = b["UpperArm." + side];
                Vector3 direction = Vector3.right * Mathf.Sign(upper.position.x - posed.transform.position.x);
                var lower = b["Forearm." + side];
                var hand = b["Hand." + side];
                upper.rotation = Quaternion.FromToRotation(lower.position - upper.position, direction) * upper.rotation;
                lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, direction) * lower.rotation;
            }
            human.human = mapping.Select(p => new HumanBone { humanName = p.Key, boneName = p.Value, limit = new HumanLimit { useDefaultValues = true } }).ToArray();
            human.skeleton = transforms.Select(t => new SkeletonBone { name = t.name, position = t.localPosition, rotation = t.localRotation, scale = t.localScale }).ToArray();
            var avatar = AvatarBuilder.BuildHumanAvatar(posed, human);
            avatar.name = instance.name + "-VRChat-Humanoid";
            if (!avatar.isValid || !avatar.isHuman) { UnityEngine.Object.DestroyImmediate(avatar); throw new Exception("Failed to build humanoid with shoulders"); }
            string avatarPath = folder + "/" + avatar.name + ".asset";
            var existing = AssetDatabase.LoadAssetAtPath<Avatar>(avatarPath);
            if (existing == null) AssetDatabase.CreateAsset(avatar, avatarPath);
            else { EditorUtility.CopySerialized(avatar, existing); UnityEngine.Object.DestroyImmediate(avatar); avatar = existing; EditorUtility.SetDirty(existing); }
            instance.AddComponent<Animator>().avatar = avatar;
        } finally { UnityEngine.Object.DestroyImmediate(posed); }
    }
}
