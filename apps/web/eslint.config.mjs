import nextVitals from "eslint-config-next/core-web-vitals";

const config = [
  ...nextVitals,
  {
    // The locally bundled MediaPipe Emscripten runtime is generated third-party code.
    ignores: [".next/**", "node_modules/**", "public/mediapipe/wasm/**"],
  },
];

export default config;
