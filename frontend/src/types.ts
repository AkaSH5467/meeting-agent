export type BriefStatus = "pending" | "done" | "no_company" | "error";

export interface RecentNews {
  headline: string;
  date?: string;
  source?: string;
}

export interface TechSignals {
  domain_tags: string[];
  notable_tools: string[];
  summary: string;
}

export interface TalkingPoint {
  point: string;
  rationale?: string;
}

export interface BriefOutput {
  company_name: string;
  domain: string;
  what_they_do: string;
  company_stage?: string;
  founded?: string;
  headcount_range?: string;
  recent_news: RecentNews[];
  funding?: string;
  tech_signals: TechSignals;
  pain_points: string[];
  talking_points: TalkingPoint[];
  confidence: "high" | "medium" | "low";
  data_gaps: string[];
}

export interface Meeting {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  attendees: string[];
  company_name?: string;
  domain?: string;
  brief_status: BriefStatus;
  created_at: string;
  brief?: BriefOutput;
}

export interface Brief {
  id: number;
  meeting_id: string;
  data: BriefOutput;
  confidence?: string;
  created_at: string;
}

export interface MeetingBriefStatus {
  meeting_id: string;
  status: BriefStatus;
  brief?: BriefOutput;
  error_message?: string;
}

export interface GoogleUser {
  email: string;
  name: string;
  picture: string;
  sub: string;
}