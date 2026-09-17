using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineLocalCoach : UdonSharpBehaviour
{
    public Transform carriage, seatAnchor;
    public Transform arrivalDrop, castleDrop;
    public Vector3[] outbound, inbound;
    public float outboundLength, inboundLength;
    public DomaineSeatAllocation allocation;
    public Animator horses;
    public Transform[] wheels;
    public UnityEngine.UI.Text status;
    public bool atCastle;
    public bool riding;
    public float cruiseSpeed = 2f;
    public float seatViewHeight = 2.48f;
    private float distance, speed;
    private bool returning, boarding, finishing;
    private float boardDeadline;
    private DomainePassengerSeat activeSeat;
    private Quaternion[] wheelRest;
    private float wheelAngle;
    private void Start()
    {
        wheelRest = new Quaternion[wheels.Length];
        for (int i = 0; i < wheels.Length; i++) wheelRest[i] = wheels[i].localRotation;
        Place(0f, false); UpdateLabel();
    }
    public void BoardAtArrival() { Board(false); }
    public void BoardAtCastle() { Board(true); }
    public override void Interact() { Board(atCastle); }
    private void Board(bool fromCastle)
    {
        if (riding || boarding || !Utilities.IsValid(Networking.LocalPlayer)) return;
        int index = allocation.LocalSeatIndex();
        if (index < 0) { status.text = "Preparation du carrosse... Reessayez dans un instant."; return; }
        activeSeat = allocation.seats[index];
        // Assignment serialization can arrive before the station ownership transfer.
        if (!Networking.IsOwner(activeSeat.gameObject)) Networking.SetOwner(Networking.LocalPlayer, activeSeat.gameObject);
        if (!Networking.IsOwner(activeSeat.gameObject)) { status.text = "Preparation de votre place..."; return; }
        atCastle = fromCastle; returning = fromCastle;
        distance = 0f; speed = 0f; Place(0f, returning);
        Vector3 localSeat = seatAnchor.localPosition;
        localSeat.y = seatViewHeight - (Networking.LocalPlayer.GetTrackingData(VRCPlayerApi.TrackingDataType.Head).position.y - Networking.LocalPlayer.GetPosition().y);
        seatAnchor.localPosition = localSeat;
        boarding = true; boardDeadline = Time.time + 5f;
        activeSeat.Board();
    }
    public void Seated()
    {
        if (!boarding) return;
        boarding = false; riding = true;
        horses.Play("HorseWalk", 0, 0f); UpdateLabel();
        SendCustomEventDelayedSeconds(nameof(CalibrateView), .5f);
    }
    public void CalibrateView()
    {
        if (!riding || !Utilities.IsValid(Networking.LocalPlayer)) return;
        float headY = Networking.LocalPlayer.GetTrackingData(VRCPlayerApi.TrackingDataType.Head).position.y;
        Vector3 p = seatAnchor.localPosition;
        p.y += carriage.position.y + seatViewHeight - headY;
        seatAnchor.localPosition = p;
    }
    private void Update()
    {
        if (boarding && Time.time > boardDeadline) { boarding = false; UpdateLabel(); }
        if (!riding) return;
        float length = returning ? inboundLength : outboundLength;
        float dt = Mathf.Min(Time.deltaTime, .1f);
        float target = Mathf.Min(cruiseSpeed, Mathf.Sqrt(Mathf.Max(0f, 2f * .45f * (length - distance))));
        speed = Mathf.MoveTowards(speed, target, .45f * dt);
        float previousDistance = distance;
        distance = Mathf.Min(length, distance + speed * dt);
        Place(distance, returning); horses.speed = Mathf.Max(.1f, speed / 1.0833333f);
        wheelAngle += distance - previousDistance;
        if (length - distance < .02f) Finish(!returning);
    }
    private void LateUpdate()
    {
        if (wheelRest == null) return;
        // FBX wheels lie in their local XZ plane. Preserve the final angle at rest.
        for (int i = 0; i < wheels.Length; i++)
            wheels[i].localRotation = wheelRest[i] * Quaternion.AngleAxis(-wheelAngle / (i < 2 ? .612f : .782f) * Mathf.Rad2Deg, Vector3.up);
    }
    public Vector3 Point(float meters, bool back)
    {
        Vector3[] points = back ? inbound : outbound;
        float length = back ? inboundLength : outboundLength;
        float t = Mathf.Clamp01(meters / length) * (points.Length - 1);
        int i = Mathf.Min(points.Length - 2, Mathf.FloorToInt(t));
        return Vector3.Lerp(points[i], points[i + 1], t - i);
    }
    public void Place(float meters, bool back)
    {
        Vector3 p = Point(meters, back);
        Vector3 direction = Point(meters + .5f, back) - Point(Mathf.Max(0f, meters - .5f), back);
        carriage.SetPositionAndRotation(p, Quaternion.LookRotation(direction, Vector3.up) * Quaternion.Euler(0f, 90f, 0f));
    }
    public void ExitRide()
    {
        // Retained for old serialized callers. Passengers cannot end a journey.
    }
    private void Finish(bool castle)
    {
        atCastle = castle; riding = false; boarding = false; finishing = true;
        activeSeat.Leave();
        // Station exit placement is applied by VRChat; teleport on the next frame.
        SendCustomEventDelayedFrames(nameof(CompleteExit), 1);
    }
    public void Unseated()
    {
        if (finishing) return;
        if (riding) SendCustomEventDelayedFrames(nameof(ResumeSeat), 1);
        else boarding = false;
    }
    public void ResumeSeat()
    {
        // Avatar reloads can emit station-exit events without ending the journey.
        if (riding && !finishing && Utilities.IsValid(Networking.LocalPlayer)) activeSeat.Board();
    }
    public void CompleteExit()
    {
        if (!finishing) return;
        Transform destination = atCastle ? castleDrop : arrivalDrop;
        if (Utilities.IsValid(Networking.LocalPlayer)) Networking.LocalPlayer.TeleportTo(destination.position, destination.rotation);
        finishing = false; riding = false; boarding = false; speed = 0f;
        Place(atCastle ? outboundLength : 0f, false);
        horses.speed = 1f; horses.Play("HorseIdle", 0, 0f);
        UpdateLabel();
    }
    public override void OnPlayerRespawn(VRCPlayerApi player)
    {
        if (!player.isLocal) return;
        if (riding || boarding) Finish(false);
        else { atCastle = false; Place(0f, false); UpdateLabel(); }
    }
    private void UpdateLabel()
    {
        status.text = riding ? (returning ? "Retour a l'accueil" : "Voyage vers le chateau")
            : (atCastle ? "Carrosse royal - retour a l'accueil" : "Carrosse royal - depart pour le chateau");
    }
}
