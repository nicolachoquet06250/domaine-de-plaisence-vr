using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using VRC.SDK3.Components;
using VRC.Udon;
using Object = UnityEngine.Object;

public static class AddDomaineAvatarPortraits
{
    public const string RootName = "Accueil - Choisir son avatar";
    public const string MaleId = "avtr_0807b909-3a7f-49c1-8e22-dac3d8907d70";
    public const string FemaleId = "avtr_be271bee-5f21-4966-a8c5-b345468c18cf";
    public const string TextureRoot = "Assets/DomainePlaisance/Interactions/Textures/Avatars";
    const string PedestalPrefab = "Packages/com.vrchat.worlds/Samples/UdonExampleScene/Prefabs/AvatarPedestal.prefab";
    static readonly Color Gold = new Color32(205, 177, 113, 255);
    static readonly Color Green = new Color32(22, 49, 42, 255);
    public static void Require(bool ok, string message) { if (!ok) throw new Exception(message); }

    [MenuItem("Domaine/Accueil/Ajouter les portraits d'avatars")]
    public static void Run()
    {
        try {
            Directory.CreateDirectory("DomaineImportReports");
            var backup = "DomaineImportReports/scene-before-avatar-portraits-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".unity.backup";
            File.Copy(SetupDomaineInteractions.ScenePath, backup, false);
            ConfigureDomaineAvatarGate.EnsureProgram();
            var scene = EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
            var parent = GameObject.Find("Interactions du Domaine");
            Require(parent, "Interaction root missing");
            int stations = Object.FindObjectsOfType<VRCStation>(true).Length;
            var previous = parent.transform.Find(RootName);
            if (previous) Object.DestroyImmediate(previous.gameObject);
            foreach (var name in new[] { "homme", "femme" }) {
                var path = TextureRoot + "/" + name + "-pose-royale.png";
                var importer = (TextureImporter)AssetImporter.GetAtPath(path);
                Require(importer != null, "Missing portrait " + path);
                importer.textureType = TextureImporterType.Default;
                importer.sRGBTexture = true;
                importer.alphaSource = TextureImporterAlphaSource.None;
                importer.mipmapEnabled = true;
                importer.streamingMipmaps = true;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.filterMode = FilterMode.Trilinear;
                importer.npotScale = TextureImporterNPOTScale.None;
                importer.maxTextureSize = 2048;
                importer.textureCompression = TextureImporterCompression.CompressedHQ;
                importer.SaveAndReimport();
            }
            var root = new GameObject(RootName);
            root.transform.SetParent(parent.transform, false);
            // Arrival looks toward -Z. Canvas fronts face +Z, so local -X is visitor-left.
            root.transform.SetPositionAndRotation(new Vector3(0, 1.70f, -4f), Quaternion.Euler(0, 180, 0));
            CreatePortrait(root.transform, "Homme - cliquer pour porter cet avatar", "homme", MaleId, -0.69f, "CHOISIR L'AVATAR HOMME");
            CreatePortrait(root.transform, "Femme - cliquer pour porter cet avatar", "femme", FemaleId, 0.69f, "CHOISIR L'AVATAR FEMME");
            ConfigureDomaineAvatarGate.FindArrivalPortal().SetActive(false);
            Canvas.ForceUpdateCanvases();
            EditorSceneManager.MarkSceneDirty(scene);
            Require(EditorSceneManager.SaveScene(scene), "Scene save failed");
            AssetDatabase.SaveAssets();
            EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
            ValidateSaved();
            Require(Object.FindObjectsOfType<VRCStation>(true).Length == stations, "Station count changed");
            Canvas.ForceUpdateCanvases();
            ValidateDomaineInteractions.Preview("avatars-sous-arche-contexte.png", new Vector3(0, 1.72f, 2.3f), new Vector3(0, 2.05f, -4), 64);
            ValidateDomaineInteractions.Preview("avatars-sous-arche-detail.png", new Vector3(0, 1.70f, -0.55f), rootPosition(), 42);
            File.WriteAllText("DomaineImportReports/avatar-portraits-static.json", "{\"passed\":true,\"savedAndReopened\":true,\"centeredUnderArch\":true,\"left\":\"" + MaleId + "\",\"right\":\"" + FemaleId + "\",\"position\":[0,1.7,-4],\"eachCardMetres\":[1.16,1.9],\"unchangedStations\":" + stations + ",\"localAvatarChoiceProgram\":true}");
            Debug.Log("DOMAINE_AVATAR_PORTRAITS_SAVED");
            if (Application.isBatchMode) ValidateDomaineAvatarPortraits.Run();
        } catch (Exception e) { Debug.LogException(e); if (Application.isBatchMode) EditorApplication.Exit(1); else throw; }
    }
    static Vector3 rootPosition() { return GameObject.Find(RootName).transform.position; }
    static RectTransform Rect(string name, Transform parent, Vector2 position, Vector2 size) {
        var go = new GameObject(name, typeof(RectTransform));
        var rect = (RectTransform)go.transform;
        rect.SetParent(parent, false); rect.anchoredPosition = position; rect.sizeDelta = size;
        return rect;
    }
    static void Flat(string name, Transform parent, Vector2 position, Vector2 size, Color color) {
        var image = Rect(name, parent, position, size).gameObject.AddComponent<Image>();
        image.color = color; image.raycastTarget = false;
    }
    static void CreatePortrait(Transform parent, string name, string textureName, string id, float x, string label) {
        // Reuse the SDK's compiled Interact -> SetAvatarUse(LocalPlayer) program.
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PedestalPrefab);
        Require(prefab, "VRChat pedestal example missing");
        var card = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        PrefabUtility.UnpackPrefabInstance(card, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
        card.name = name; card.transform.SetParent(parent, false); card.transform.localPosition = new Vector3(x, 0, 0);
        Object.DestroyImmediate(card.GetComponent<MeshRenderer>());
        Object.DestroyImmediate(card.GetComponent<MeshFilter>());
        var collider = card.GetComponent<BoxCollider>();
        collider.size = new Vector3(1.16f, 1.9f, .04f); collider.center = Vector3.zero; collider.isTrigger = true;
        var pedestal = card.GetComponent<VRCAvatarPedestal>();
        pedestal.blueprintId = id; pedestal.ChangeAvatarsOnUse = true;
        // This is a portrait selector: no additional native 3D avatar display.
        var placement = new GameObject("Emplacement natif sans apercu 3D").transform;
        placement.SetParent(card.transform, false); placement.localScale = Vector3.zero;
        pedestal.Placement = placement; pedestal.scale = 0;
        var udon = card.GetComponent<UdonBehaviour>();
        udon.interactText = textureName == "homme" ? "Porter l'avatar homme" : "Porter l'avatar femme";
        udon.proximity = 3f;
        var canvasRect = Rect("Portrait et legende", card.transform, Vector2.zero, new Vector2(1160, 1900));
        canvasRect.localScale = Vector3.one * .001f;
        var canvas = canvasRect.gameObject.AddComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace;
        Flat("Cadre dore", canvasRect, Vector2.zero, new Vector2(1160, 1900), Gold);
        Flat("Fond vert", canvasRect, Vector2.zero, new Vector2(1136, 1876), Green);
        var portrait = Rect("Screenshot " + textureName, canvasRect, new Vector2(0, 95), new Vector2(1100, 1650)).gameObject.AddComponent<RawImage>();
        portrait.texture = AssetDatabase.LoadAssetAtPath<Texture2D>(TextureRoot + "/" + textureName + "-pose-royale.png");
        portrait.raycastTarget = false;
        var text = Rect("Choisir cet avatar", canvasRect, new Vector2(0, -831), new Vector2(1100, 145)).gameObject.AddComponent<Text>();
        text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); text.fontSize = 55;
        text.text = label; text.color = Gold; text.alignment = TextAnchor.MiddleCenter;
        text.raycastTarget = false; text.supportRichText = false;
        text.font.RequestCharactersInTexture(label, text.fontSize, FontStyle.Normal);
        foreach (var transform in card.GetComponentsInChildren<Transform>(true)) transform.gameObject.layer = 0;
        ConfigureDomaineAvatarGate.ConfigurePortrait(pedestal, ConfigureDomaineAvatarGate.FindArrivalPortal());
    }
    public static void ValidateSaved() {
        var root = GameObject.Find(RootName);
        Require(root && root.activeInHierarchy, "Portrait group missing");
        Require(Vector3.Distance(root.transform.position, new Vector3(0, 1.7f, -4)) < .001f, "Group not centered under arch");
        var pedestals = root.GetComponentsInChildren<VRCAvatarPedestal>();
        Require(pedestals.Length == 2, "Exactly two selectors required");
        var male = pedestals.Single(p => p.blueprintId == MaleId);
        var female = pedestals.Single(p => p.blueprintId == FemaleId);
        var arrival = GameObject.Find("Arrivee visiteurs").transform;
        var viewerRight = arrival.right;
        Require(Vector3.Dot(male.transform.position - female.transform.position, viewerRight) < 0, "Male must be on visitor-left");
        Require(Mathf.Abs(male.transform.position.x + female.transform.position.x) < .001f, "Pair not horizontally centered");
        Physics.SyncTransforms();
        foreach (var pedestal in pedestals) {
            var collider = pedestal.GetComponent<BoxCollider>();
            Require(collider && collider.enabled && collider.isTrigger, "Missing non-blocking interaction surface");
            Require(pedestal.ChangeAvatarsOnUse, "Avatar switching disabled");
            var udon = pedestal.GetComponent<UdonBehaviour>();
            Require(udon && udon.enabled && udon.programSource && udon.ProgramSize > 0 && udon.proximity == 3, "Compiled interaction program missing");
            Require(AssetDatabase.GetAssetPath(udon.programSource).EndsWith("DomaineAvatarChoice.asset"), "Unexpected interaction program");
            var image = pedestal.GetComponentInChildren<RawImage>();
            string expected = pedestal == male ? "homme" : "femme";
            Require(image && image.texture && AssetDatabase.GetAssetPath(image.texture) == TextureRoot + "/" + expected + "-pose-royale.png", "Portrait mismatch");
            Require(Mathf.Abs(image.rectTransform.rect.width / image.rectTransform.rect.height - 2f / 3) < .0001f, "Portrait aspect distorted");
            Require(Vector3.Dot(-image.transform.forward, arrival.position - image.transform.position) > 0, "Portrait faces away from spawn");
            var eye = new Vector3(pedestal.transform.position.x, 1.7f, -1.6f);
            Require(Physics.Raycast(eye, (pedestal.transform.position - eye).normalized, out var hit, 3f, 1, QueryTriggerInteraction.Collide) && hit.collider == collider, "Portrait interaction ray blocked");
        }
    }
}

