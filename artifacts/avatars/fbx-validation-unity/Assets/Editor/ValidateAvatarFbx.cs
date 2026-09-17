using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class ValidateAvatarFbx
{
    [Serializable] public class Result {
        public string asset;
        public bool validHumanoid;
        public int renderers;
        public int blendShapes;
        public string[] clips;
        public string[] warnings;
    }
    [Serializable] public class Report { public Result[] avatars; }
    public static void Run() {
        try {
            var results = new[] { "courtMale", "courtFemale" }.Select(name => {
                string path = "Assets/Avatars/" + name + "/" + name + ".fbx";
                var importer = (ModelImporter)AssetImporter.GetAtPath(path);
                importer.animationType = ModelImporterAnimationType.Human;
                importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                importer.importBlendShapes = true;
                importer.SaveAndReimport();
                var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                var avatar = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Avatar>().FirstOrDefault();
                var renderers = model.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                var result = new Result {
                    asset = name,
                    validHumanoid = avatar != null && avatar.isValid && avatar.isHuman,
                    renderers = renderers.Length,
                    blendShapes = renderers.Sum(r => r.sharedMesh.blendShapeCount),
                    clips = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>()
                        .Where(c => !c.name.StartsWith("__preview__")).Select(c => c.name).ToArray(),
                    warnings = importer.GetImportWarnings()
                };
                Debug.Log("AVATAR_FBX_VALIDATED " + JsonUtility.ToJson(result));
                return result;
            }).ToArray();
            File.WriteAllText("../fbx/verification-unity.json", JsonUtility.ToJson(new Report { avatars = results }, true));
            EditorApplication.Exit(results.All(r => r.validHumanoid && r.blendShapes == 15 && r.clips.Length == 4) ? 0 : 2);
        } catch (Exception ex) { Debug.LogException(ex); EditorApplication.Exit(1); }
    }
}
