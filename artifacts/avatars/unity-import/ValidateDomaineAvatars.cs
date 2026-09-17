using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using VRC.SDK3.Avatars.Components;
using VRC.SDKBase;

public static class ValidateDomaineAvatars
{
    public static void Run() {
        try {
            foreach (var name in new[] { "courtMale", "courtFemale" }) Validate(name);
            File.WriteAllText("Logs/domaine-avatars-validation.txt", "PASS: both saved prefabs; humanoid anatomy and shoulder hierarchy; 15 serialized visemes per avatar; actual skinned vertex deformation for every viseme; materials and texture references; no missing scripts; no blueprint IDs.\n");
            Debug.Log("DOMAINE_AVATARS_VALIDATION_PASS");
            EditorApplication.Exit(0);
        } catch (Exception e) {
            File.WriteAllText("Logs/domaine-avatars-validation.txt", e.ToString());
            Debug.LogException(e);
            EditorApplication.Exit(1);
        }
    }
    static void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
    static void Validate(string name) {
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/DomaineAvatars/" + name + "/" + name + "-VRChat.prefab");
        Check(prefab != null, name + ": prefab missing");
        var instance = UnityEngine.Object.Instantiate(prefab);
        var neutral = new Mesh();
        var speech = new Mesh();
        try {
            var animator = instance.GetComponent<Animator>();
            Check(animator != null && animator.avatar != null && animator.avatar.isHuman && animator.avatar.isValid, name + ": invalid humanoid");
            var source = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/DomaineAvatars/" + name + "/" + name + ".fbx");
            foreach (var original in source.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("Arm") || t.name.Contains("Hand") || t.name == "Head" || t.name == "Hips")) {
                var match = instance.GetComponentsInChildren<Transform>(true).Single(t => t.name == original.name);
                Check(Vector3.Distance(match.position, original.position) < 0.0001f && Quaternion.Angle(match.rotation, original.rotation) < 0.1f, name + ": bind pose changed for " + original.name);
            }
            foreach (var bone in new[] { HumanBodyBones.Hips, HumanBodyBones.Spine, HumanBodyBones.Chest, HumanBodyBones.Neck, HumanBodyBones.Head, HumanBodyBones.LeftShoulder, HumanBodyBones.RightShoulder, HumanBodyBones.LeftHand, HumanBodyBones.RightHand, HumanBodyBones.LeftFoot, HumanBodyBones.RightFoot })
                Check(animator.GetBoneTransform(bone) != null, name + ": missing " + bone);
            var chest = animator.GetBoneTransform(HumanBodyBones.Chest);
            foreach (var bone in new[] { HumanBodyBones.LeftShoulder, HumanBodyBones.RightShoulder, HumanBodyBones.Neck })
                Check(animator.GetBoneTransform(bone).parent == chest, name + ": invalid chest hierarchy");
            var hips = animator.GetBoneTransform(HumanBodyBones.Hips);
            foreach (var bone in new[] { HumanBodyBones.LeftHand, HumanBodyBones.RightHand, HumanBodyBones.LeftFoot, HumanBodyBones.RightFoot })
                Check(animator.GetBoneTransform(bone).IsChildOf(hips), name + ": split humanoid hierarchy");
            var descriptor = instance.GetComponent<VRCAvatarDescriptor>();
            Check(descriptor != null && descriptor.lipSync == VRC_AvatarDescriptor.LipSyncStyle.VisemeBlendShape, name + ": lip sync mode");
            var face = descriptor.VisemeSkinnedMesh;
            Check(face != null && face.transform.IsChildOf(instance.transform), name + ": missing face reference");
            string[] expected = { "sil", "PP", "FF", "TH", "DD", "kk", "CH", "SS", "nn", "RR", "aa", "E", "I", "O", "U" };
            Check(descriptor.VisemeBlendShapes.SequenceEqual(expected.Select(v => "viseme_" + v)), name + ": incorrect viseme order");
            face.BakeMesh(neutral);
            var baseline = neutral.vertices;
            foreach (string viseme in descriptor.VisemeBlendShapes) {
                int index = face.sharedMesh.GetBlendShapeIndex(viseme);
                Check(index >= 0, name + ": missing " + viseme);
                face.SetBlendShapeWeight(index, 100);
                face.BakeMesh(speech);
                var vertices = speech.vertices;
                Check(vertices.Where((vertex, i) => (vertex - baseline[i]).sqrMagnitude > 1e-12f).Any(), name + ": no skinned deformation for " + viseme);
                face.SetBlendShapeWeight(index, 0);
            }
            foreach (var transform in instance.GetComponentsInChildren<Transform>(true))
                Check(GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(transform.gameObject) == 0, name + ": missing script");
            foreach (var material in instance.GetComponentsInChildren<Renderer>(true).SelectMany(r => r.sharedMaterials)) {
                Check(material != null && material.shader != null && material.shader.name == "Standard", name + ": invalid material");
                Check(AssetDatabase.GetAssetPath(material).EndsWith(".mat"), name + ": material not extracted");
                if (material.IsKeywordEnabled("_NORMALMAP")) Check(material.GetTexture("_BumpMap") != null, name + ": missing normal map");
            }
            Check(instance.GetComponent<VRC.Core.PipelineManager>() != null && string.IsNullOrEmpty(instance.GetComponent<VRC.Core.PipelineManager>().blueprintId), name + ": unexpected blueprint binding");
            Debug.Log("VALIDATED " + name + ": humanoid hierarchy and all 15 baked visemes");
        } finally {
            UnityEngine.Object.DestroyImmediate(instance);
            UnityEngine.Object.DestroyImmediate(neutral);
            UnityEngine.Object.DestroyImmediate(speech);
        }
    }
}
