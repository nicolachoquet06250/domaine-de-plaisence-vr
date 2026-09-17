Shader "Domaine/PBR" {
 Properties {
  _Color ("Couleur", Color) = (1,1,1,1)
  _MainTex ("Couleur et alpha", 2D) = "white" {}
  _Metallic ("Metal", Range(0,1)) = 0
  _Glossiness ("Lissage", Range(0,1)) = 0.5
  _BumpMap ("Normales", 2D) = "bump" {}
  _BumpScale ("Force des normales", Float) = 1
  [HDR] _EmissionColor ("Emission", Color) = (0,0,0,1)
  _EmissionMap ("Texture emission", 2D) = "white" {}
  _AlphaClip ("Decoupe alpha", Float) = 0
  _Cutoff ("Seuil alpha", Range(0,1)) = 0.5
  [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Faces", Float) = 2
 }
 SubShader {
  Tags { "RenderType"="Opaque" }
  LOD 300
  Cull [_Cull]
  CGPROGRAM
  #pragma surface surf Standard fullforwardshadows addshadow
  #pragma target 3.0
  #include "UnityStandardUtils.cginc"
  sampler2D _MainTex, _BumpMap, _EmissionMap;
  fixed4 _Color;
  half _Metallic, _Glossiness, _BumpScale, _AlphaClip, _Cutoff;
  half4 _EmissionColor;
  struct Input { float2 uv_MainTex; float2 uv_BumpMap; float2 uv_EmissionMap; };
  void surf(Input IN, inout SurfaceOutputStandard o) {
   fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color;
   if(_AlphaClip>0.5) clip(c.a-_Cutoff);
   o.Albedo=c.rgb; o.Alpha=c.a;
   o.Metallic=_Metallic; o.Smoothness=_Glossiness;
   o.Normal=UnpackScaleNormal(tex2D(_BumpMap,IN.uv_BumpMap),_BumpScale);
   o.Emission=tex2D(_EmissionMap,IN.uv_EmissionMap).rgb*_EmissionColor.rgb;
  }
  ENDCG
 }
 FallBack "Diffuse"
}
