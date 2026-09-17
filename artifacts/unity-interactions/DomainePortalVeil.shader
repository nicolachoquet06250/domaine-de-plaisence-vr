Shader "Domaine/Voile du portail" {
 Properties { _Color ("Voile turquoise", Color) = (.439216,.776471,.792157,.21) }
 SubShader {
  Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
  Blend SrcAlpha OneMinusSrcAlpha
  ZWrite Off
  Cull Off
  Pass {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #include "UnityCG.cginc"
   fixed4 _Color;
   struct appdata { float4 vertex:POSITION; };
   struct v2f { float4 position:SV_POSITION; };
   v2f vert(appdata v) { v2f o; o.position=UnityObjectToClipPos(v.vertex); return o; }
   fixed4 frag(v2f i):SV_Target { return _Color; }
   ENDCG
  }
 }
}
