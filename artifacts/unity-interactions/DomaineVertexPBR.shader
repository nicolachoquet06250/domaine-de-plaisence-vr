Shader "Domaine/PBR Vertex" {
 Properties {
  _Color ("Couleur", Color) = (1,1,1,1)
  _MainTex ("Couleur", 2D) = "white" {}
  _BumpMap ("Normales", 2D) = "bump" {}
  _Metallic ("Metal", Range(0,1)) = 0
  _Glossiness ("Lissage", Range(0,1)) = .5
  _UseVertexColor ("Couleurs des sommets", Float) = 0
 }
 SubShader {
  Tags { "RenderType"="Opaque" }
  Cull Off
  CGPROGRAM
  #pragma surface surf Standard fullforwardshadows addshadow
  #pragma target 3.0
  sampler2D _MainTex, _BumpMap;
  fixed4 _Color;
  half _Metallic, _Glossiness, _UseVertexColor;
  struct Input { float2 uv_MainTex; float2 uv_BumpMap; float4 color:COLOR; };
  void surf(Input IN, inout SurfaceOutputStandard o) {
   fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color;
   c.rgb*=lerp(float3(1,1,1),IN.color.rgb,_UseVertexColor);
   o.Albedo=c.rgb; o.Alpha=1; o.Metallic=_Metallic; o.Smoothness=_Glossiness;
   o.Normal=UnpackNormal(tex2D(_BumpMap,IN.uv_BumpMap));
  }
  ENDCG
 }
 FallBack "Diffuse"
}
