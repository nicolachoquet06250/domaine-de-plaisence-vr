using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class DomaineFountain : UdonSharpBehaviour
{
    public SkinnedMeshRenderer[] surfaces;
    public float[] durations;
    public float[] phases;
    private int[] previous;
    private int[] counts;
    private double animationTime;
    private void Start()
    {
        InitializeShapes();
        animationTime = (Networking.GetServerTimeInSeconds() % 4d + 4d) % 4d;
    }
    private void InitializeShapes()
    {
        previous = new int[surfaces.Length]; counts = new int[surfaces.Length];
        for (int i = 0; i < surfaces.Length; i++)
        {
            surfaces[i].updateWhenOffscreen = true;
            counts[i] = surfaces[i].sharedMesh.blendShapeCount;
            for (int j = 0; j < counts[i]; j++) surfaces[i].SetBlendShapeWeight(j, 0f);
            previous[i] = -1;
        }
    }
    private void Update()
    {
        // Advance a bounded clock smoothly even when the network clock adjusts.
        animationTime = (animationTime + Time.deltaTime) % 4d;
        SampleTime(animationTime);
    }
    public void SampleTime(double seconds)
    {
        if (previous == null) InitializeShapes();
        for (int i = 0; i < surfaces.Length; i++)
        {
            int n = counts[i]; if (n == 0) continue;
            double duration = durations[i]; if (duration <= 0d) continue;
            double wrapped = ((seconds + phases[i]) % duration + duration) % duration;
            float phase = (float)(wrapped / duration * n);
            if (phase >= n) phase = 0f;
            int a = Mathf.FloorToInt(phase) % n; int b = (a + 1) % n;
            int old = previous[i];
            if (old >= 0) { surfaces[i].SetBlendShapeWeight(old, 0f); surfaces[i].SetBlendShapeWeight((old + 1) % n, 0f); }
            surfaces[i].SetBlendShapeWeight(a, (1f - (phase - Mathf.Floor(phase))) * 100f);
            surfaces[i].SetBlendShapeWeight(b, (phase - Mathf.Floor(phase)) * 100f); previous[i] = a;
        }
    }
}
