# HeadAudio

Source: https://github.com/met4citizen/HeadAudio
Pinned revision: `d3af5f9ff86ab6b2b1913d411a4e1922ec101953`.

`headworklet.mjs` is the unmodified upstream `dist/headworklet.min.mjs`.
`model-en-mixed.bin` is the upstream mixed-voice English acoustic model.
Both are distributed under the included MIT license. Regenerate with
`node scripts/vendor-headaudio.mjs` from the project root.

The application wrapper in `src/speech-visemes.ts` decodes the model and maps
the worklet's viseme indices to the Blender morph target names. No network
speech service is used; these two files are served with the application.
