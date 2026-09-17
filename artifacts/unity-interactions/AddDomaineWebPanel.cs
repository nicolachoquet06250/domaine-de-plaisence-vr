using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using Object = UnityEngine.Object;

public static class AddDomaineWebPanel
{
    const string Url = "https://test-iwsdk.nicovers06.fr";
    const string PanelName = "Accueil - Decouvrir la version web";
    const string TexturePath = "Assets/DomainePlaisance/Interactions/Textures/version-web-qr.png";
    static readonly Color Gold = new Color32(205, 177, 113, 255);
    static readonly Color Cream = new Color32(250, 242, 221, 255);
    static Font font;

    static RectTransform Rect(string name, Transform parent, Vector2 position, Vector2 size)
    {
        var go = new GameObject(name, typeof(RectTransform));
        var rt = (RectTransform)go.transform;
        rt.SetParent(parent, false);
        rt.sizeDelta = size;
        rt.anchoredPosition = position;
        return rt;
    }
    static void Image(string name, Transform parent, Vector2 position, Vector2 size, Color color)
    {
        var image = Rect(name, parent, position, size).gameObject.AddComponent<Image>();
        image.color = color;
        image.raycastTarget = false;
    }
    static Text Label(string name, Transform parent, string value, Vector2 position, Vector2 size, int fontSize, Color color, TextAnchor alignment = TextAnchor.MiddleLeft)
    {
        var text = Rect(name, parent, position, size).gameObject.AddComponent<Text>();
        text.font = font;
        text.fontSize = fontSize;
        text.text = value;
        text.color = color;
        text.alignment = alignment;
        text.raycastTarget = false;
        text.supportRichText = false;
        text.horizontalOverflow = HorizontalWrapMode.Wrap;
        text.verticalOverflow = VerticalWrapMode.Truncate;
        font.RequestCharactersInTexture(value, fontSize, FontStyle.Normal);
        return text;
    }
    static void Require(bool valid, string message) { if (!valid) throw new Exception(message); }

    [MenuItem("Domaine/Accueil/Ajouter le panneau version web")]
    public static void Run()
    {
        try
        {
            var scene = EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
            Directory.CreateDirectory("DomaineImportReports");
            File.Copy(SetupDomaineInteractions.ScenePath, "DomaineImportReports/scene-before-web-panel.unity.backup", true);
            var parent = GameObject.Find("Interactions du Domaine");
            Require(parent, "Interaction root missing");
            int stationsBefore = Object.FindObjectsOfType<VRC.SDK3.Components.VRCStation>(true).Length;
            var old = parent.transform.Find(PanelName);
            if (old) Object.DestroyImmediate(old.gameObject);

            var importer = (TextureImporter)AssetImporter.GetAtPath(TexturePath);
            Require(importer != null, "QR texture missing");
            importer.textureType = TextureImporterType.Default;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.mipmapEnabled = false;
            importer.filterMode = FilterMode.Point;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.maxTextureSize = 1024;
            importer.SaveAndReimport();

            var root = new GameObject(PanelName);
            root.transform.SetParent(parent.transform, false);
            // Facing the columns from the arrival spawn, screen-right is Unity -X.
            // The right column is x=-2.6, z=-4; the panel sits beyond its plinth.
            root.transform.SetPositionAndRotation(new Vector3(-4.15f, 1.7f, -4f), Quaternion.Euler(0, 180, 0));
            var canvasRect = Rect("Panneau rectangulaire", root.transform, Vector2.zero, new Vector2(1600, 850));
            canvasRect.localScale = Vector3.one * .001f;
            var canvas = canvasRect.gameObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.WorldSpace;
            canvas.sortingOrder = 0;
            font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            Image("Cadre dore", canvasRect, Vector2.zero, new Vector2(1600, 850), Gold);
            Image("Fond vert", canvasRect, Vector2.zero, new Vector2(1584, 834), new Color32(22, 49, 42, 255));
            Label("Invitation", canvasRect, "LE DOMAINE, AUSSI SUR LE WEB", new Vector2(0, 321), new Vector2(1380, 70), 40, Gold);
            Image("Filet dore", canvasRect, new Vector2(0, 261), new Vector2(1380, 2), Gold);
            Label("Titre", canvasRect, "Prolongez la visite\ndans votre navigateur", new Vector2(-210, 135), new Vector2(960, 180), 62, Cream);
            Label("Description", canvasRect, "Découvrez la version web\ndu Domaine de Plaisance.", new Vector2(-210, -55), new Vector2(960, 125), 38, Cream);
            var qr = Rect("QR code - version web", canvasRect, new Vector2(530, 55), new Vector2(340, 340)).gameObject.AddComponent<RawImage>();
            qr.texture = AssetDatabase.LoadAssetAtPath<Texture2D>(TexturePath);
            qr.raycastTarget = false;
            Label("Scanner", canvasRect, "Scannez pour visiter", new Vector2(530, -155), new Vector2(410, 55), 30, Cream, TextAnchor.MiddleCenter);
            Image("Filet adresse", canvasRect, new Vector2(0, -222), new Vector2(1380, 2), Gold);
            Label("Adresse web", canvasRect, Url, new Vector2(0, -295), new Vector2(1380, 90), 49, Gold, TextAnchor.MiddleCenter);
            EnableDomaineWebLink.Configure(root);
            Canvas.ForceUpdateCanvases();
            foreach (var label in root.GetComponentsInChildren<Text>())
                Require(label.preferredHeight <= label.rectTransform.rect.height + 1, "Clipped label: " + label.name);

            EditorSceneManager.MarkSceneDirty(scene);
            Require(EditorSceneManager.SaveScene(scene), "Failed to save scene");
            AssetDatabase.SaveAssets();
            scene = EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
            root = GameObject.Find(PanelName);
            Require(root && root.activeInHierarchy, "Panel not saved");
            Require(root.GetComponentsInChildren<Text>().Single(t => t.name == "Adresse web").text == Url, "URL mismatch");
            Require(root.transform.position.x + .8f < -3.025f, "Panel overlaps right column");
            Require(Vector3.Dot(-root.transform.forward, Vector3.forward) > .99f, "Panel faces away from arrival");
            Require(Object.FindObjectsOfType<VRC.SDK3.Components.VRCStation>(true).Length == stationsBefore, "Station count changed");
            Canvas.ForceUpdateCanvases();
            ValidateDomaineInteractions.Preview("accueil-panneau-web-contexte.png", new Vector3(0, 1.7f, 2.3f), new Vector3(-1.2f, 1.9f, -4), 68);
            ValidateDomaineInteractions.Preview("accueil-panneau-web-detail.png", new Vector3(-4.15f, 1.7f, -1.9f), root.transform.position, 37);
            File.WriteAllText("DomaineImportReports/panneau-web-validation.json", "{\"passed\":true,\"url\":\"" + Url + "\",\"worldPosition\":[-4.15,1.7,-4],\"sizeMetres\":[1.6,0.85],\"rightOfRightColumn\":true,\"savedAndReopened\":true,\"stationCountUnchanged\":true,\"linkAccess\":\"visible URL and scannable QR code\"}");
            Debug.Log("DOMAINE_WEB_PANEL_SUCCESS " + Url);
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }
        catch (Exception e)
        {
            Debug.LogException(e);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            else throw;
        }
    }
}
