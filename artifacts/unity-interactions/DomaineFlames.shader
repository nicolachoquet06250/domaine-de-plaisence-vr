Shader "Domaine/Flammes vivantes"
{
    Properties
    {
        _Speed("Vitesse", Float) = 1.65
        _Intensity("Intensite", Float) = 1.2
        _Phase("Variation du foyer", Float) = 0
        [HideInInspector] _TestTime("Temps de verification (-1 = automatique)", Float) = -1
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
        Blend SrcAlpha One
        ZWrite Off
        Cull Off
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "UnityCG.cginc"
            float _Speed, _Intensity, _Phase, _TestTime;
            struct appdata { float4 vertex:POSITION; float2 uv:TEXCOORD0; float2 seed:TEXCOORD1; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct v2f { float4 pos:SV_POSITION; float2 uv:TEXCOORD0; float seed:TEXCOORD1; UNITY_VERTEX_OUTPUT_STEREO };
            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v); UNITY_INITIALIZE_OUTPUT(v2f,o); UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.pos=UnityObjectToClipPos(v.vertex);o.uv=v.uv;o.seed=v.seed.x;return o;
            }
            float hash(float2 p) { return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453); }
            float noise(float2 p)
            {
                float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);
                return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);
            }
            fixed4 frag(v2f i):SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
                float t=(_TestTime>=0?_TestTime:_Time.y)*_Speed+i.seed+_Phase;
                float2 p=float2(i.uv.x-.5,i.uv.y);
                float n=noise(float2(p.x*5+i.seed,p.y*4-t));
                float detail=noise(float2(p.x*13-i.seed,p.y*9-t*1.7));
                float sway=sin(p.y*7-t*1.8)*.1*p.y+(n-.5)*.22*p.y;
                float density=.43*pow(max(0,1-p.y),.85)-abs(p.x+sway)+(n-.5)*.17+(detail-.5)*.055;
                float alpha=smoothstep(-.035,.065,density)*smoothstep(0,.1,p.y)*(1-smoothstep(.73,1,p.y));
                clip(alpha-.012);
                float core=smoothstep(.035,.30,density)*(1-p.y);
                float3 color=lerp(float3(1.9,.19,.009),float3(3,2,.65),core)*_Intensity;
                return float4(color,alpha*.68);
            }
            ENDCG
        }
    }
}
