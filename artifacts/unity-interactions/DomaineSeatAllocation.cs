using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// The carriage is local. Only invisible passenger stations have network poses,
// so VRChat can represent seated avatars without sharing one occupied station.
[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class DomaineSeatAllocation : UdonSharpBehaviour
{
    public DomainePassengerSeat[] seats;
    [UdonSynced] public int[] passengerIds = new int[100];
    private VRCPlayerApi[] players = new VRCPlayerApi[100];
    private float nextRefresh;
    private float nextClaim;
    private void Update()
    {
        if (Time.time >= nextClaim)
        {
            nextClaim = Time.time + .5f;
            int localIndex = LocalSeatIndex();
            if (localIndex >= 0 && !Networking.IsOwner(seats[localIndex].gameObject))
                Networking.SetOwner(Networking.LocalPlayer, seats[localIndex].gameObject);
        }
        if (!Networking.IsOwner(gameObject) || Time.time < nextRefresh) return;
        nextRefresh = Time.time + 2f;
        RefreshAssignments();
    }
    public void RefreshAssignments()
    {
        if (!Networking.IsOwner(gameObject)) return;
        bool changed = false;
        for (int i = 0; i < passengerIds.Length; i++)
            if (passengerIds[i] != 0 && !Utilities.IsValid(VRCPlayerApi.GetPlayerById(passengerIds[i])))
            { passengerIds[i] = 0; changed = true; }
        VRCPlayerApi.GetPlayers(players);
        for (int p = 0; p < players.Length; p++)
        {
            VRCPlayerApi player = players[p]; if (!Utilities.IsValid(player)) continue;
            bool found = false;
            for (int i = 0; i < passengerIds.Length; i++) if (passengerIds[i] == player.playerId)
            {
                found = true;
                if (!Networking.IsOwner(player, seats[i].gameObject)) Networking.SetOwner(player, seats[i].gameObject);
            }
            if (found) continue;
            for (int i = 0; i < passengerIds.Length; i++) if (passengerIds[i] == 0)
            {
                passengerIds[i] = player.playerId;
                Networking.SetOwner(player, seats[i].gameObject); changed = true; break;
            }
        }
        if (changed) RequestSerialization();
    }
    public int LocalSeatIndex()
    {
        if (!Utilities.IsValid(Networking.LocalPlayer)) return -1;
        int id = Networking.LocalPlayer.playerId;
        for (int i = 0; i < passengerIds.Length; i++) if (passengerIds[i] == id) return i;
        return -1;
    }
    public override void OnPlayerJoined(VRCPlayerApi player) { RefreshAssignments(); }
    public override void OnPlayerLeft(VRCPlayerApi player) { nextRefresh = 0f; }
    public override void OnOwnershipTransferred(VRCPlayerApi player) { nextRefresh = 0f; }
}
