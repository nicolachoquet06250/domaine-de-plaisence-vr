using UdonSharp;
using UnityEngine;
using VRC.SDK3.Components;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineAvatarChoice : UdonSharpBehaviour
{
    public VRCAvatarPedestal pedestal;
    public GameObject arrivalPortal;

    public override void Interact()
    {
        VRCPlayerApi player = Networking.LocalPlayer;
        if (!Utilities.IsValid(player) || !Utilities.IsValid(pedestal) || !Utilities.IsValid(arrivalPortal)) return;
        pedestal.SetAvatarUse(player);
        // SetActive is local. No synced variable or network event is involved.
        // Keep the portal unlocked for this visit, including after avatar reloads/respawns.
        arrivalPortal.SetActive(true);
    }
}
