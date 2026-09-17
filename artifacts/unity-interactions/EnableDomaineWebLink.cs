using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using VRC.SDK3.Components;
using Object = UnityEngine.Object;

public static class EnableDomaineWebLink
{
    public const string Url = "https://test-iwsdk.nicovers06.fr";
    const string RootName = "Accueil - Decouvrir la version web";
    static void Require(bool ok,string message) { if(!ok) throw new Exception(message); }
    public static void Configure(GameObject root)
    {
        var canvas=root.GetComponentInChildren<Canvas>();
        Require(canvas,"Missing reception panel canvas");
        var canvasObject=canvas.gameObject;
        if(!canvasObject.GetComponent<GraphicRaycaster>()) canvasObject.AddComponent<GraphicRaycaster>();
        if(!canvasObject.GetComponent<VRCUiShape>()) canvasObject.AddComponent<VRCUiShape>();
        var collider=canvasObject.GetComponent<BoxCollider>();
        if(!collider) collider=canvasObject.AddComponent<BoxCollider>();
        collider.center=Vector3.zero;collider.size=new Vector3(1600,850,15);collider.isTrigger=true;
        foreach(var t in canvas.GetComponentsInChildren<Transform>(true)) t.gameObject.layer=0;
        if(!Object.FindObjectOfType<EventSystem>())
        {
            var events=new GameObject("EventSystem UI du Domaine",typeof(EventSystem),typeof(StandaloneInputModule));
            events.transform.SetParent(root.transform.parent,false);
        }
        var label=root.GetComponentsInChildren<Text>().Single(t=>t.name=="Adresse web");
        var existing=canvas.transform.Find("Lien web - cliquer pour copier");
        if(existing)
        {
            label.transform.SetParent(canvas.transform,false);
            Object.DestroyImmediate(existing.gameObject);
        }
        var go=new GameObject("Lien web - cliquer pour copier",typeof(RectTransform),typeof(Image),typeof(InputField));
        var rect=(RectTransform)go.transform;rect.SetParent(canvas.transform,false);
        rect.sizeDelta=new Vector2(1410,98);rect.anchoredPosition=new Vector2(0,-287);
        var image=go.GetComponent<Image>();image.color=new Color32(35,72,60,255);image.raycastTarget=true;
        label.transform.SetParent(rect,false);label.rectTransform.sizeDelta=new Vector2(1360,88);label.rectTransform.anchoredPosition=Vector2.zero;
        label.raycastTarget=false;label.fontSize=47;label.horizontalOverflow=HorizontalWrapMode.Overflow;
        var field=go.GetComponent<InputField>();field.textComponent=label;field.targetGraphic=image;
        field.contentType=InputField.ContentType.Standard;field.lineType=InputField.LineType.SingleLine;
        field.readOnly=false;field.interactable=true;field.characterLimit=256;
        field.navigation=new Navigation{mode=Navigation.Mode.None};field.text=Url;
        field.selectionColor=new Color(.75f,.65f,.36f,.5f);
        var colors=field.colors;colors.highlightedColor=new Color(1.2f,1.2f,1.2f,1);colors.selectedColor=colors.highlightedColor;field.colors=colors;
        // VRChat's native keyboard handles Copy. Restore the shared invitation
        // after a visitor closes their local text editor; never claim it copied.
        var setter=(UnityAction<string>)Delegate.CreateDelegate(typeof(UnityAction<string>),field,typeof(InputField).GetProperty("text").GetSetMethod());
        UnityEventTools.AddStringPersistentListener(field.onEndEdit,setter,Url);
        var placeholder=Object.Instantiate(label,rect);placeholder.name="Adresse de la version web";placeholder.text="Adresse de la version web";placeholder.color=new Color(.8f,.8f,.8f,.6f);field.placeholder=placeholder;
        var oldHint=canvas.transform.Find("Aide copie du lien");if(oldHint)Object.DestroyImmediate(oldHint.gameObject);
        var hint=Object.Instantiate(label,canvas.transform);hint.name="Aide copie du lien";
        hint.rectTransform.anchoredPosition=new Vector2(0,-375);hint.rectTransform.sizeDelta=new Vector2(1410,52);
        hint.fontSize=29;hint.text="Cliquez sur l’adresse, puis sur Copier dans le clavier.";
        hint.color=new Color32(250,242,221,255);hint.raycastTarget=false;
        field.ForceLabelUpdate();Canvas.ForceUpdateCanvases();
    }
    [MenuItem("Domaine/Accueil/Activer la copie du lien web")]
    public static void Run()
    {
        try
        {
            var scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            var root=GameObject.Find(RootName);Require(root,"Reception panel missing");
            if(!File.Exists("DomaineImportReports/scene-before-web-copy.unity.backup")) File.Copy(SetupDomaineInteractions.ScenePath,"DomaineImportReports/scene-before-web-copy.unity.backup");
            var nodes=VRC.Udon.Editor.UdonEditorManager.Instance.GetNodeDefinitions().Select(n=>n.fullName).ToArray();
            var clipboard=nodes.Where(n=>n.IndexOf("clipboard",StringComparison.OrdinalIgnoreCase)>=0||n.IndexOf("systemCopyBuffer",StringComparison.OrdinalIgnoreCase)>=0).ToArray();
            File.WriteAllText("DomaineImportReports/udon-clipboard-exposure.json",JsonUtility.ToJson(new Exposure{directClipboardNodes=clipboard},true));
            Debug.Log("UDON_DIRECT_CLIPBOARD_NODES "+clipboard.Length);
            Configure(root);
            EditorSceneManager.MarkSceneDirty(scene);Require(EditorSceneManager.SaveScene(scene),"Scene save failed");
            scene=EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            root=GameObject.Find(RootName);var canvas=root.GetComponentInChildren<Canvas>();var field=root.GetComponentInChildren<InputField>();
            Require(field&&field.text==Url&&field.interactable&&!field.readOnly,"Clickable URL not saved");
            Require(canvas.GetComponent<VRCUiShape>()&&canvas.GetComponent<GraphicRaycaster>()&&canvas.GetComponent<BoxCollider>(),"Missing native UI components");
            Require(field.onEndEdit.GetPersistentMethodName(0)=="set_text","Missing reset event");
            field.onEndEdit.SetPersistentListenerState(0,UnityEventCallState.EditorAndRuntime);
            field.text="test local";field.onEndEdit.Invoke(field.text);Require(field.text==Url,"URL not restored after edit");
            field.onEndEdit.SetPersistentListenerState(0,UnityEventCallState.RuntimeOnly);
            // Verify that both physics and Unity's UI raycast reach the URL.
            var cameraObject=new GameObject("Verification clic lien web",typeof(Camera));var camera=cameraObject.GetComponent<Camera>();
            camera.transform.position=new Vector3(-4.15f,1.7f,-1.9f);camera.transform.LookAt(root.transform.position);camera.nearClipPlane=.05f;
            canvas.worldCamera=camera;
            var renderTexture=new RenderTexture(900,600,24);camera.targetTexture=renderTexture;
            Canvas.ForceUpdateCanvases();camera.Render();Physics.SyncTransforms();
            var target=field.transform.position;var ray=new Ray(camera.transform.position,(target-camera.transform.position).normalized);
            Require(Physics.Raycast(ray,out var hit,4f,~0,QueryTriggerInteraction.Collide)&&hit.collider==canvas.GetComponent<BoxCollider>(),"UI blocked by another collider");
            var pointer=new PointerEventData(Object.FindObjectOfType<EventSystem>()){position=camera.WorldToScreenPoint(target)};
            var results=new List<RaycastResult>();canvas.GetComponent<GraphicRaycaster>().Raycast(pointer,results);
            Debug.Log("WEB_UI_RAYCAST "+pointer.position+" depth="+field.targetGraphic.depth+" results="+string.Join(",",results.Select(r=>r.gameObject.name)));
            Require(results.Any(r=>r.gameObject==field.gameObject),"URL does not receive UI clicks");
            canvas.worldCamera=null;camera.targetTexture=null;renderTexture.Release();Object.DestroyImmediate(renderTexture);Object.DestroyImmediate(cameraObject);
            ValidateDomaineInteractions.Preview("accueil-lien-copiable.png",new Vector3(-4.15f,1.7f,-1.9f),root.transform.position,37);
            // Reload so temporary validation changes do not affect the saved scene.
            EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath,OpenSceneMode.Single);
            File.WriteAllText("DomaineImportReports/lien-copiable-validation.json","{\"passed\":true,\"url\":\""+Url+"\",\"nativeUiShape\":true,\"pointerRaycast\":true,\"restoresUrlAfterEdit\":true,\"savedAndReopened\":true,\"directOneClickClipboard\":false,\"flow\":\"Click URL, then Copy in VRChat keyboard\",\"liveVRChatTested\":false}");
            Debug.Log("DOMAINE_WEB_COPY_CONFIGURED");EditorApplication.Exit(0);
        }
        catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}
    }
    [Serializable] public class Exposure{public string[] directClipboardNodes;}
}
