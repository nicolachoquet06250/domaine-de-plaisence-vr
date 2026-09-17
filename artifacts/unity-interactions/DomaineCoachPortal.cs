using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineCoachPortal : UdonSharpBehaviour
{
    public DomaineLocalCoach coach;
    public int destination;
    public GameObject visual;
    public Collider passage;
    private float nextAttempt;
    private float nextPositionCheck;
    private void Update()
    {
        bool available = !coach.riding;
        if (visual.activeSelf != available) visual.SetActive(available);
        if (passage.enabled != available) passage.enabled = available;
        // Foot position also works for tiny avatars and missed trigger events.
        if (available && Time.time >= nextPositionCheck && Utilities.IsValid(Networking.LocalPlayer))
        {
            nextPositionCheck = Time.time + .1f;
            Vector3 p = transform.InverseTransformPoint(Networking.LocalPlayer.GetPosition());
            if (Mathf.Abs(p.x) <= 1f && p.y >= -.5f && p.y <= 4f && p.z >= -1.3f && p.z <= .6f) Enter();
        }
    }
    private void Enter()
    {
        if (coach.riding || Time.time < nextAttempt) return;
        nextAttempt = Time.time + .75f;
        if (destination == 0) coach.BoardAtArrival();
        else coach.BoardAtCastle();
    }
    public override void Interact() { Enter(); }
    public override void OnPlayerTriggerEnter(VRCPlayerApi player)
    {
        if (Utilities.IsValid(player) && player.isLocal) Enter();
    }
    public override void OnPlayerTriggerStay(VRCPlayerApi player)
    {
        // Retry if the local player's station was still being allocated on entry.
        if (Utilities.IsValid(player) && player.isLocal) Enter();
    }
}
