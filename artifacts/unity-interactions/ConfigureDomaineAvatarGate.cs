using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using VRC.SDK3.Components;
using VRC.Udon;
using Object = UnityEngine.Object;

public static class ConfigureDomaineAvatarGate
{
    const string ProgramPath = SetupDomaineInteractions.Root + "/Scripts/DomaineAvatarChoice.asset";
    public static void EnsureProgram() {
        if (!AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(ProgramPath)) {
            var program = ScriptableObject.CreateInstance<UdonSharpProgramAsset>();
            program.sourceCsScript = AssetDatabase.LoadAssetAtPath<MonoScript>(SetupDomaineInteractions.Root + "/Scripts/DomaineAvatarChoice.cs");
            AssetDatabase.CreateAsset(program, ProgramPath);
        }
        AssetDatabase.SaveAssets();
        UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
        if (AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(ProgramPath).SerializedProgramAsset.RetrieveProgram() == null)
            throw new Exception("Avatar choice Udon compilation failed");
    }
    public static GameObject FindArrivalPortal() {
        return Object.FindObjectsOfType<DomaineCoachPortal>(true).Single(p => p.destination == 0 && p.name == "Depart royal").gameObject;
    }
    public static void ConfigurePortrait(VRCAvatarPedestal pedestal, GameObject portal) {
        var choice = pedestal.GetComponent<DomaineAvatarChoice>();
        if (!choice) {
            // Replace only the previous SDK pedestal graph, keeping the collider and portrait.
            foreach (var old in pedestal.GetComponents<UdonBehaviour>()) {
                if (!old.programSource || !AssetDatabase.GetAssetPath(old.programSource).EndsWith("AvatarPedestal Program.asset"))
                    throw new Exception("Unexpected existing portrait program: " + pedestal.name);
                Object.DestroyImmediate(old);
            }
            choice = pedestal.gameObject.AddUdonSharpComponent<DomaineAvatarChoice>();
        }
        choice.pedestal = pedestal; choice.arrivalPortal = portal;
        var udon = UdonSharpEditorUtility.GetBackingUdonBehaviour(choice);
        udon.interactText = pedestal.blueprintId == AddDomaineAvatarPortraits.MaleId ? "Porter l'avatar homme" : "Porter l'avatar femme";
        udon.proximity = 3f;
        UdonSharpEditorUtility.CopyProxyToUdon(choice);
        EditorUtility.SetDirty(choice); EditorUtility.SetDirty(udon);
    }
    public static void ValidateSaved() {
        var portal = FindArrivalPortal();
        if (portal.activeSelf || portal.activeInHierarchy) throw new Exception("Arrival portal must start inactive");
        var returning = Object.FindObjectsOfType<DomaineCoachPortal>(true).Single(p => p.destination == 1);
        if (!returning.gameObject.activeInHierarchy) throw new Exception("Return portal was disabled");
        var portraits = GameObject.Find(AddDomaineAvatarPortraits.RootName).GetComponentsInChildren<DomaineAvatarChoice>();
        if (portraits.Length != 2) throw new Exception("Two avatar choice behaviours required");
        foreach (var choice in portraits) {
            var udon = UdonSharpEditorUtility.GetBackingUdonBehaviour(choice);
            if (choice.arrivalPortal != portal || choice.pedestal != choice.GetComponent<VRCAvatarPedestal>()) throw new Exception("Wrong portrait references");
            if (choice.GetComponents<UdonBehaviour>().Length != 1 || udon.ProgramSize == 0 || udon.SyncMethod != VRC.SDKBase.Networking.SyncType.None) throw new Exception("Choice must have one compiled, unsynchronized behaviour");
        }
        if (portal.GetComponent<VRC.SDK3.Components.VRCObjectSync>() || portal.GetComponent<VRCObjectPool>()) throw new Exception("Portal must not have network object synchronization");
    }
    [MenuItem("Domaine/Accueil/Portail local apres choix d'avatar")]
    public static void Run() {
        try {
            Directory.CreateDirectory("DomaineImportReports");
            File.Copy(SetupDomaineInteractions.ScenePath, "DomaineImportReports/scene-before-avatar-gate-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".unity.backup", false);
            EnsureProgram();
            var scene = EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
            var portal = FindArrivalPortal();
            foreach (var pedestal in GameObject.Find(AddDomaineAvatarPortraits.RootName).GetComponentsInChildren<VRCAvatarPedestal>()) ConfigurePortrait(pedestal, portal);
            portal.SetActive(false);
            EditorSceneManager.MarkSceneDirty(scene);
            if (!EditorSceneManager.SaveScene(scene)) throw new Exception("Scene save failed");
            AssetDatabase.SaveAssets();
            EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
            ValidateSaved(); AddDomaineAvatarPortraits.ValidateSaved();
            File.WriteAllText("DomaineImportReports/avatar-gate-static.json", "{\"passed\":true,\"arrivalInactiveByDefault\":true,\"returnPortalUnchanged\":true,\"twoLocalUnsynchronizedChoices\":true,\"savedAndReopened\":true}");
            Debug.Log("DOMAINE_AVATAR_GATE_SAVED");
            if (Application.isBatchMode) ValidateDomaineAvatarGate.Run();
        } catch (Exception e) { Debug.LogException(e); if (Application.isBatchMode) EditorApplication.Exit(1); else throw; }
    }
}
