using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineMirrorVisibility : UdonSharpBehaviour
{
    public GameObject[] mirrors;
    public float maxDistance = 12f;
    private float nextCheck;
    private void Update()
    {
        if (Time.time < nextCheck || !Utilities.IsValid(Networking.LocalPlayer)) return;
        nextCheck = Time.time + .2f;
        Vector3 head = Networking.LocalPlayer.GetTrackingData(VRCPlayerApi.TrackingDataType.Head).position;
        for (int i = 0; i < mirrors.Length; i++)
        {
            Transform mirror = mirrors[i].transform;
            Vector3 offset = head - mirror.position;
            bool visible = offset.sqrMagnitude < maxDistance * maxDistance && Vector3.Dot(offset, -mirror.forward) > .02f && Mathf.Abs(offset.y) < 2.6f;
            if (mirrors[i].activeSelf != visible) mirrors[i].SetActive(visible);
        }
    }
}
