using UdonSharp;
using UnityEngine;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineCoachButton : UdonSharpBehaviour
{
    public DomaineLocalCoach coach;
    public int action;
    public override void Interact()
    {
        if (action == 0) coach.BoardAtArrival();
        else if (action == 1) coach.BoardAtCastle();
        else coach.ExitRide();
    }
}
