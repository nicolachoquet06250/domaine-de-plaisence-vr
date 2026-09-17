using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineBenchSeat : UdonSharpBehaviour
{
    public VRC.SDK3.Components.VRCStation station;
    private VRCPlayerApi occupant;
    public override void Interact()
    {
        if (Utilities.IsValid(occupant) || !Utilities.IsValid(Networking.LocalPlayer)) return;
        station.UseStation(Networking.LocalPlayer);
    }
    public override void OnStationEntered(VRCPlayerApi player) { occupant = player; }
    public override void OnStationExited(VRCPlayerApi player)
    {
        if (occupant == player) occupant = null;
    }
    public override void OnPlayerLeft(VRCPlayerApi player)
    {
        if (occupant == player) occupant = null;
    }
}
