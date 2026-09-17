using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineJump : UdonSharpBehaviour
{
    public float jumpImpulse = 3.5f;

    private void Start() { ApplyJump(); }

    public void ApplyJump()
    {
        if (!Utilities.IsValid(Networking.LocalPlayer))
        {
            SendCustomEventDelayedSeconds(nameof(ApplyJump), .5f);
            return;
        }
        Networking.LocalPlayer.SetJumpImpulse(jumpImpulse);
    }

    public override void OnPlayerJoined(VRCPlayerApi player)
    {
        if (player.isLocal) ApplyJump();
    }

    public override void OnPlayerRespawn(VRCPlayerApi player)
    {
        if (player.isLocal) ApplyJump();
    }
}
