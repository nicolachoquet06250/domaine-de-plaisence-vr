using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class InspectDomaineAvatars {
    public static void Run() {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.65f, 0.65f, 0.65f);
        var report = new StringBuilder();
        for (int i = 0; i < 2; i++) {
            var name = i == 0 ? "courtMale" : "courtFemale";
            var folder = "Assets/DomaineAvatars/" + name + "/";
            var original = UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(folder + name + ".fbx"));
            var configured = UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(folder + name + "-VRChat.prefab"));
            foreach (var bone in original.GetComponentsInChildren<Transform>().Where(t => t.name.Contains("Arm") || t.name == "Head" || t.name == "Hips" || t.name == "Chest")) {
                var match = configured.GetComponentsInChildren<Transform>().First(t => t.name == bone.name);
                report.AppendLine(name + " " + bone.name + " original=" + bone.position.ToString("F5") + " prefab=" + match.position.ToString("F5") + " rotDiff=" + Quaternion.Angle(bone.rotation, match.rotation));
            }
            original.transform.position = new Vector3(-0.5f,0,0);
            configured.transform.position = new Vector3(0.5f,0,0);
            var light = new GameObject("Light").AddComponent<Light>();
            light.type = LightType.Directional; light.intensity = 1.1f;
            light.transform.rotation = Quaternion.Euler(25,155,0);
            var camera = new GameObject("Camera").AddComponent<Camera>();
            camera.transform.position = new Vector3(0,1.0f,3.7f); camera.transform.LookAt(new Vector3(0,0.95f,0));
            camera.fieldOfView = 35; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = Color.gray;
            var rt = new RenderTexture(1200,1000,24); camera.targetTexture = rt; camera.Render(); RenderTexture.active = rt;
            var tex = new Texture2D(1200,1000,TextureFormat.RGB24,false); tex.ReadPixels(new Rect(0,0,1200,1000),0,0); tex.Apply();
            File.WriteAllBytes("Logs/" + name + "-compare.png",tex.EncodeToPNG());
            camera.targetTexture=null; RenderTexture.active=null; rt.Release();
            UnityEngine.Object.DestroyImmediate(rt); UnityEngine.Object.DestroyImmediate(tex);
            UnityEngine.Object.DestroyImmediate(original); UnityEngine.Object.DestroyImmediate(configured);
            UnityEngine.Object.DestroyImmediate(camera.gameObject); UnityEngine.Object.DestroyImmediate(light.gameObject);
        }
        File.WriteAllText("Logs/domaine-avatar-pose.txt",report.ToString());
        EditorApplication.Exit(0);
    }
}
