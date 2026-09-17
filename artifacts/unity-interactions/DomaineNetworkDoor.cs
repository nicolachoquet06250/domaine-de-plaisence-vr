using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
using VRC.Udon.Common.Interfaces;

[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class DomaineNetworkDoor : UdonSharpBehaviour
{
    public Transform leftHinge, rightHinge;
    public Collider doorwayBlocker;
    public float duration = 1.4f;
    public float openAngle = 105f;
    [UdonSynced] private bool targetOpen;
    [UdonSynced] private float fromProgress;
    [UdonSynced] private double changedAt;
    private VRCPlayerApi[] players = new VRCPlayerApi[100];
    private float nextScan, lastPresence;
    public float CurrentProgress()
    {
        float elapsed = Mathf.Max(0f, (float)(Networking.GetServerTimeInSeconds() - changedAt));
        return Mathf.MoveTowards(fromProgress, targetOpen ? 1f : 0f, elapsed / duration);
    }
    private void Update()
    {
        ApplyProgress(CurrentProgress());
        if (!Networking.IsOwner(gameObject) || Time.time < nextScan) return;
        nextScan = Time.time + .15f;
        VRCPlayerApi.GetPlayers(players);
        bool near = false;
        for (int i = 0; i < players.Length; i++)
        {
            VRCPlayerApi p = players[i];
            if (!Utilities.IsValid(p)) continue;
            Vector3 v = transform.InverseTransformPoint(p.GetPosition());
            if (v.y > -.3f && v.y < 3.8f && Mathf.Abs(v.x) < 1.9f && Mathf.Abs(v.z) < 3.2f) near = true;
        }
        if (near) lastPresence = Time.time;
        bool desired = near || Time.time - lastPresence < 2f;
        if (desired != targetOpen) SetOpen(desired);
    }
    public void ApplyProgress(float progress)
    {
        float eased = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(progress));
        leftHinge.localRotation = Quaternion.Euler(0f, -openAngle * eased, 0f);
        rightHinge.localRotation = Quaternion.Euler(0f, openAngle * eased, 0f);
        doorwayBlocker.enabled = progress < .85f;
    }
    private void SetOpen(bool value)
    {
        fromProgress = CurrentProgress(); changedAt = Networking.GetServerTimeInSeconds();
        targetOpen = value; RequestSerialization();
    }
    public override void Interact() { SendCustomNetworkEvent(NetworkEventTarget.Owner, nameof(RequestOpen)); }
    public void RequestOpen()
    {
        if (!Networking.IsOwner(gameObject)) return;
        lastPresence = Time.time;
        if (!targetOpen) SetOpen(true);
    }
    public override void OnDeserialization() { ApplyProgress(CurrentProgress()); }
    public override void OnOwnershipTransferred(VRCPlayerApi player)
    {
        if (player.isLocal) { lastPresence = Time.time; nextScan = 0f; }
    }
}
