export type CameraDeviceLike = { deviceId: string; label: string; groupId?: string };
export type CameraRoleSelection = {
  primaryId: string;
  secondaryId: string;
  primaryLabel: string;
  secondaryLabel: string;
  confirmedAt: string;
};

const ROLE_STORAGE_KEY = "serps_validated_camera_roles_v1";
const IDENTITY_STORAGE_KEY = "serps_identity_camera_v1";
const PRIMARY_TERMS = ["integrated", "front", "built-in", "builtin", "internal", "user"];
const SECONDARY_TERMS = ["usb", "external", "rear", "environment"];

function score(label: string, terms: string[]): number {
  const value = label.toLowerCase();
  return terms.reduce((total, term) => total + (value.includes(term) ? 1 : 0), 0);
}

function available(deviceId: string, devices: CameraDeviceLike[]): boolean {
  return !!deviceId && devices.some((device) => device.deviceId === deviceId);
}

export function recommendCameraRoles(
  devices: CameraDeviceLike[],
  previous: CameraRoleSelection | null = null,
): { primaryId: string; secondaryId: string; reason: string; ambiguous: boolean } {
  if (
    previous
    && previous.primaryId !== previous.secondaryId
    && available(previous.primaryId, devices)
    && available(previous.secondaryId, devices)
  ) {
    return {
      primaryId: previous.primaryId,
      secondaryId: previous.secondaryId,
      reason: "Previous validated camera-role selection restored. Confirm both assignments before use.",
      ambiguous: false,
    };
  }
  const rankedPrimary = devices.map((device) => ({ device, value: score(device.label, PRIMARY_TERMS) })).sort((left, right) => right.value - left.value);
  const rankedSecondary = devices.map((device) => ({ device, value: score(device.label, SECONDARY_TERMS) })).sort((left, right) => right.value - left.value);
  const primary = rankedPrimary[0];
  const secondary = rankedSecondary.find((item) => item.device.deviceId !== primary?.device.deviceId);
  const primaryUnambiguous = !!primary && primary.value > 0 && rankedPrimary.filter((item) => item.value === primary.value).length === 1;
  const secondaryUnambiguous = !!secondary && secondary.value > 0 && rankedSecondary.filter((item) => item.value === secondary.value).length === 1;
  if (!primaryUnambiguous || !secondaryUnambiguous) {
    return {
      primaryId: primaryUnambiguous ? primary.device.deviceId : "",
      secondaryId: secondaryUnambiguous ? secondary.device.deviceId : "",
      reason: "Camera labels are ambiguous. Select the candidate-facing and environmental cameras manually, then confirm.",
      ambiguous: true,
    };
  }
  return {
    primaryId: primary.device.deviceId,
    secondaryId: secondary.device.deviceId,
    reason: "Semantic label matching selected candidate-facing and environmental cameras. Confirm before use.",
    ambiguous: false,
  };
}

export function readCameraRoles(): CameraRoleSelection | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem(ROLE_STORAGE_KEY) ?? "null") as CameraRoleSelection | null;
  } catch {
    return null;
  }
}

export function persistCameraRoles(selection: CameraRoleSelection): void {
  localStorage.setItem(ROLE_STORAGE_KEY, JSON.stringify(selection));
  localStorage.setItem(IDENTITY_STORAGE_KEY, JSON.stringify({
    deviceId: selection.primaryId,
    label: selection.primaryLabel,
    confirmedAt: selection.confirmedAt,
  }));
}

export function readIdentityCamera<T extends CameraDeviceLike>(devices: T[]): T | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = JSON.parse(localStorage.getItem(IDENTITY_STORAGE_KEY) ?? "null") as { deviceId?: string } | null;
    if (stored?.deviceId) {
      const match = devices.find((device) => device.deviceId === stored.deviceId);
      if (match) return match;
    }
  } catch {
    // Fall through to semantic label matching.
  }
  const recommendation = recommendCameraRoles(devices);
  return recommendation.primaryId ? devices.find((device) => device.deviceId === recommendation.primaryId) ?? null : null;
}

export function persistIdentityCamera(device: CameraDeviceLike): void {
  localStorage.setItem(IDENTITY_STORAGE_KEY, JSON.stringify({
    deviceId: device.deviceId,
    label: device.label,
    confirmedAt: new Date().toISOString(),
  }));
}

export function cameraLabel(device: CameraDeviceLike | null | undefined, fallback = "Unselected camera"): string {
  return device?.label?.trim() || fallback;
}
