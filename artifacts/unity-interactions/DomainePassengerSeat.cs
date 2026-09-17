using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
using VRC.SDK3.Components;

[UdonBehaviourSyncMode(BehaviourSyncMode.Continuous)]
public class DomainePassengerSeat : UdonSharpBehaviour
{
    public DomaineLocalCoach coach;
    public VRC.SDK3.Components.VRCStation station;
    public VRCObjectSync poseSync;
    private bool localSeated;
    public void Board()
    {
        if (!Networking.IsOwner(gameObject)) return;
        transform.SetPositionAndRotation(coach.seatAnchor.position, coach.seatAnchor.rotation);
        poseSync.FlagDiscontinuity();
        station.UseStation(Networking.LocalPlayer);
    }
    private void LateUpdate()
    {
        if (localSeated) transform.SetPositionAndRotation(coach.seatAnchor.position, coach.seatAnchor.rotation);
    }
    public override void OnStationEntered(VRCPlayerApi player)
    {
        if (!player.isLocal) return;
        localSeated = true; coach.Seated();
    }
    public override void OnStationExited(VRCPlayerApi player)
    {
        if (!player.isLocal) return;
        localSeated = false; coach.Unseated();
    }
    public void Leave() { station.ExitStation(Networking.LocalPlayer); }
}
