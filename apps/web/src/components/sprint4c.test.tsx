import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import LoginPage from "../app/login/page";
import { AppNavigation } from "./AppNavigation";
import { directionSymbol, instructionFor, poseIsValid, supportsFaceDetection, type FaceObservation } from "../lib/biometrics";
import { recommendCameraRoles } from "../lib/cameraRoles";
import { deriveFaceGeometry } from "../lib/faceDetection";

describe("Sprint 4C deterministic and accessible first render", () => {
  it("does not render a client-derived demonstration indicator during SSR", () => {
    const first = renderToStaticMarkup(<LoginPage />);
    const second = renderToStaticMarkup(<LoginPage />);
    expect(first).toBe(second);
    expect(first).not.toContain("demo-indicator");
    expect(first).toContain("Institution code");
  });

  it("renders a visible, labelled navigation trigger", () => {
    const markup = renderToStaticMarkup(<AppNavigation />);
    expect(markup).toContain('aria-label="Open navigation"');
    expect(markup).toContain('title="Open navigation"');
    expect(markup).toContain("☰");
  });

  it("does not claim native face detection in a non-browser runtime", () => {
    expect(supportsFaceDetection()).toBe(false);
  });

  it("derives bounded orientation proxies from real landmark coordinates", () => {
    const landmarks = Array.from({ length: 478 }, () => ({ x: .5, y: .5, z: 0, visibility: 1 }));
    landmarks[234].x = .25; landmarks[454].x = .75; landmarks[10].y = .2; landmarks[152].y = .8;
    landmarks[33] = { x: .38, y: .4, z: 0, visibility: 1 }; landmarks[263] = { x: .62, y: .4, z: 0, visibility: 1 };
    const forward = deriveFaceGeometry(landmarks);
    expect(forward.yawEstimate).toBeCloseTo(0); expect(forward.pitchEstimate).toBeCloseTo(0); expect(forward.faceSize).toBeCloseTo(.3);
    landmarks[1].x = .4; expect(deriveFaceGeometry(landmarks).yawEstimate).toBeLessThan(-.16);
  });

  it("rejects an incorrect orientation and accepts the matching pose threshold", () => {
    const base: FaceObservation = { descriptor: Array(64).fill(.5), oneFace: true, faceCount: 1, centreX: .5, centreY: .5, lightingScore: .9, distanceScore: .9, confidence: .9, feedback: "ready", yawEstimate: 0, pitchEstimate: 0, rollEstimate: 0, processingTime: 20, boundingBox: { x: .3, y: .2, width: .4, height: .6 } };
    expect(poseIsValid("forward", base)).toBe(true); expect(poseIsValid("left", base)).toBe(false);
    expect(poseIsValid("left", { ...base, yawEstimate: .3 })).toBe(true);
  });

  it("maps semantic labels to candidate-facing primary and environmental secondary roles", () => {
    const cameras = [
      { deviceId: "usb", label: "USB Camera" },
      { deviceId: "integrated", label: "Integrated Camera" },
    ];
    expect(recommendCameraRoles(cameras)).toMatchObject({ primaryId: "integrated", secondaryId: "usb", ambiguous: false });
  });

  it("treats right as candidate-relative and does not invert detection for a mirrored preview", () => {
    const observation: FaceObservation = { descriptor: Array(64).fill(.5), oneFace: true, faceCount: 1, centreX: .5, centreY: .5, lightingScore: .9, distanceScore: .9, confidence: .9, feedback: "ready", yawEstimate: -.3, pitchEstimate: 0, rollEstimate: 0, processingTime: 20, boundingBox: { x: .3, y: .2, width: .4, height: .6 } };
    expect(poseIsValid("right", observation)).toBe(true);
    expect(poseIsValid("left", observation)).toBe(false);
    expect(directionSymbol("right")).toBe("→");
    expect(instructionFor("right")).toContain("your right shoulder");
  });
});
