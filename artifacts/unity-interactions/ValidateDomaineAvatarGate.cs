using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UdonSharpEditor;
using VRC.SDK3.ClientSim;
using VRC.SDKBase;
using VRC.Udon;
using Object = UnityEngine.Object;

[InitializeOnLoad]
public static class ValidateDomaineAvatarGate
{
    const string Key = "Domaine.AvatarGate.Validation";
    static double began, changed;
    static int step;
    static bool ending;
    static GameObject portal;
    static DomaineCoachPortal arrival, returning;
    static UdonBehaviour coach;
    static DomaineAvatarChoice[] choices;
    static List<string> checks = new List<string>(), errors = new List<string>();
    [Serializable] public class Result { public bool passed, liveMultiplayerTested, liveVRChatAvatarChangeTested; public string[] checks, errors; public string mode = "Unity ClientSim / actual Udon runtime"; }
    static ValidateDomaineAvatarGate() {
        if (SessionState.GetBool(Key, false)) { began = changed = EditorApplication.timeSinceStartup; EditorApplication.update += Tick; Application.logMessageReceived += Log; }
    }
    static void Check(bool ok, string message) { if (!ok) throw new Exception(message); }
    static void Next(string message) { checks.Add(message); Debug.Log("AVATAR_GATE_CHECK " + message); step++; changed = EditorApplication.timeSinceStartup; }
    public static void Run() {
        EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
        ConfigureDomaineAvatarGate.ValidateSaved(); AddDomaineAvatarPortraits.ValidateSaved();
        var settings = ClientSimSettings.Instance;
        settings.enableClientSim = true; settings.spawnPlayer = true; settings.localPlayerIsMaster = true; settings.hideMenuOnLaunch = true;
        SessionState.SetBool(Key, true); began = changed = EditorApplication.timeSinceStartup;
        EditorApplication.update -= Tick; EditorApplication.update += Tick;
        Application.logMessageReceived -= Log; Application.logMessageReceived += Log;
        EditorApplication.isPlaying = true;
    }
    static void Log(string message, string trace, LogType type) {
        if (errors.Count < 10 && (type == LogType.Error || type == LogType.Exception) && (message.Contains("Udon") || trace.Contains("DomaineAvatar"))) errors.Add(message);
    }
    static void Click(DomaineAvatarChoice choice) {
        var udon = UdonSharpEditorUtility.GetBackingUdonBehaviour(choice);
        Check(udon.SyncMethod == Networking.SyncType.None, "Portrait unexpectedly synchronized");
        Check(udon.GetProgramVariable("pedestal") == choice.pedestal, "Incorrect runtime avatar reference");
        Check(udon.GetProgramVariable("arrivalPortal") == portal, "Incorrect runtime portal reference");
        udon.Interact();
        Check(portal.activeSelf, "Portrait click did not unlock local portal: " + choice.pedestal.blueprintId);
    }
    static void Tick() {
        if (ending) {
            if (!EditorApplication.isPlaying && !EditorApplication.isPlayingOrWillChangePlaymode) {
                EditorSceneManager.OpenScene(SetupDomaineInteractions.ScenePath, OpenSceneMode.Single);
                try { ConfigureDomaineAvatarGate.ValidateSaved(); } catch (Exception e) { errors.Add(e.ToString()); }
                WriteReport(); EditorApplication.Exit(errors.Count == 0 ? 0 : 1);
            }
            return;
        }
        try {
            double now = EditorApplication.timeSinceStartup, elapsed = now - changed;
            if (now - began > 130) throw new Exception("Avatar gate runtime test timed out at step " + step);
            if (!EditorApplication.isPlaying || !Utilities.IsValid(Networking.LocalPlayer)) return;
            if (step == 0 && elapsed > 12) {
                arrival = Object.FindObjectsOfType<DomaineCoachPortal>(true).Single(p => p.destination == 0);
                returning = Object.FindObjectsOfType<DomaineCoachPortal>(true).Single(p => p.destination == 1);
                portal = arrival.gameObject;
                coach = UdonSharpEditorUtility.GetBackingUdonBehaviour(arrival.coach);
                choices = Object.FindObjectsOfType<DomaineAvatarChoice>().OrderBy(c => c.pedestal.blueprintId == AddDomaineAvatarPortraits.MaleId ? 0 : 1).ToArray();
                Check(choices.Length == 2, "Missing avatar choices");
                Check(!portal.activeSelf && !arrival.visual.activeInHierarchy && !arrival.passage.gameObject.activeInHierarchy, "Arrival portal visible/usable before choosing");
                Check(returning.gameObject.activeInHierarchy && returning.visual.activeInHierarchy, "Return portal was hidden");
                ValidateDomaineInteractions.Preview("portail-cache-avant-choix.png", new Vector3(-3.4f, 1.7f, 3.3f), new Vector3(-7.15f, 1.12f, 0), 52);
                ClientSimMain.SpawnRemotePlayer("Visiteur sans choix d'avatar");
                Networking.LocalPlayer.TeleportTo(new Vector3(-7.15f, .15f, 0), Quaternion.Euler(0, -90, 0));
                Next("Arrival hidden with inactive trigger; return portal remains available");
            } else if (step == 1 && elapsed > 2) {
                Check(!portal.activeSelf && !(bool)coach.GetProgramVariable("riding"), "Hidden portal boarded player or remote join unlocked it");
                Networking.LocalPlayer.TeleportTo(new Vector3(0, .15f, -1.4f), Quaternion.Euler(0, 180, 0));
                Click(choices[0]);
                Next("Hidden portal cannot board; male portrait locally activates it");
            } else if (step == 2 && elapsed > 1) {
                Check(arrival.visual.activeInHierarchy && arrival.passage.enabled, "Male choice did not restore visible usable portal");
                // Reset only in this unsaved test session to test the second choice independently.
                portal.SetActive(false); Click(choices[1]);
                Next("Female portrait independently activates the local portal");
            } else if (step == 3 && elapsed > 1) {
                Check(arrival.visual.activeInHierarchy && arrival.passage.enabled, "Female choice did not restore portal passage");
                Click(choices[1]);
                ValidateDomaineInteractions.Preview("portail-local-apres-choix.png", new Vector3(-3.4f, 1.7f, 3.3f), new Vector3(-7.15f, 1.12f, 0), 52);
                Networking.LocalPlayer.TeleportTo(new Vector3(-7.15f, .15f, 0), Quaternion.Euler(0, -90, 0));
                Next("Repeated choice keeps portal enabled; active portal rendered");
            } else if (step == 4 && elapsed > 3) {
                Check((bool)coach.GetProgramVariable("riding"), "Unlocked arrival portal did not board the coach");
                Check(!arrival.visual.activeSelf && !returning.visual.activeSelf, "Travel no longer hides portal visuals");
                Check(portal.activeSelf, "Travel lost the local unlocked state");
                Next("Unlocked portal boards the local coach and keeps existing travel visibility behavior");
                Finish();
            }
        } catch (Exception e) { errors.Add(e.ToString()); Debug.LogException(e); Finish(); }
    }
    static void WriteReport() {
        var result = new Result { passed = errors.Count == 0, checks = checks.ToArray(), errors = errors.ToArray(), liveMultiplayerTested = false, liveVRChatAvatarChangeTested = false };
        File.WriteAllText("DomaineImportReports/avatar-gate-runtime.json", JsonUtility.ToJson(result, true));
        Debug.Log("DOMAINE_AVATAR_GATE_RUNTIME " + JsonUtility.ToJson(result));
    }
    static void Finish() { ending = true; SessionState.SetBool(Key, false); Application.logMessageReceived -= Log; EditorApplication.isPlaying = false; }
}
