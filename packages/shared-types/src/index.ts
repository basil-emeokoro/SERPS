export type RiskLevel = "Low" | "Medium" | "High" | "Critical";

export type EvidenceEvent = {
  event_id: string;
  session_id: string;
  candidate_id: string;
  timestamp: string;
  source_module: string;
  event_type: string;
  risk_weight: number;
  confidence: number;
  camera_id?: string | null;
  evidence_path?: string | null;
  description: string;
};
