import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { BriefContent } from "./BriefContent";
import { MeetingCardSkeleton } from "./MeetingCardSkeleton";
import type { Meeting } from "../types";
import { clsx } from "clsx";

const API_URL = "https://meeting-intel-backend-58260327471.us-central1.run.app";

const statusColors = {
  pending: "bg-yellow-100 text-yellow-800",
  done: "bg-green-100 text-green-800",
  no_company: "bg-gray-100 text-gray-800",
  error: "bg-red-100 text-red-800",
};

interface Props {
  meetingId: string;
  onBack: () => void;
}

export function MeetingDetailPage({ meetingId, onBack }: Props) {
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_URL}/meetings/${meetingId}`);
        if (!res.ok) throw new Error("Not found");
        const m: Meeting = await res.json();

        if (m.brief_status === "done") {
          try {
            const briefRes = await fetch(`${API_URL}/meetings/${meetingId}/brief`);
            if (briefRes.ok) {
              const briefData = await briefRes.json();
              m.brief = briefData.data;
            }
          } catch { /* no brief */ }
        }
        setMeeting(m);
      } catch {
        setLoadError(true);
      }
    })();
  }, [meetingId]);

  if (loadError) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-muted-foreground">Meeting not found.</p>
          <button
            onClick={onBack}
            className="text-sm text-primary underline underline-offset-2"
          >
            ← Back to dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-3xl mx-auto">
          <div className="h-8 w-32 bg-muted rounded animate-pulse mb-6" />
          <MeetingCardSkeleton />
        </div>
      </div>
    );
  }

  const toUTC = (s: string) => new Date(s.endsWith("Z") ? s : s + "Z");
  const startTime = toUTC(meeting.start_time);
  const endTime = toUTC(meeting.end_time);

  return (
    <div className="min-h-screen bg-background">
      {/* Top bar */}
      <div className="border-b bg-card/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-3 flex items-center gap-4">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </button>
          <span className="text-muted-foreground/40">|</span>
          <span className="text-sm font-medium truncate">{meeting.title}</span>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">

        <div className="space-y-3">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-2xl font-bold leading-snug">{meeting.title}</h1>
            <Badge className={clsx(statusColors[meeting.brief_status], "shrink-0 text-xs capitalize")}>
              {meeting.brief_status === "done" ? "Ready" : meeting.brief_status === "pending" ? "Researching…" : meeting.brief_status === "no_company" ? "No company" : "Error"}
            </Badge>
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{startTime.toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", weekday: "long", year: "numeric", month: "long", day: "numeric" })}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{startTime.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "numeric", minute: "2-digit", hour12: true })} – {endTime.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "numeric", minute: "2-digit", hour12: true })}</span>
            </div>
            {meeting.company_name && (
              <div className="flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <span className="font-medium text-foreground">{meeting.company_name}</span>
                {meeting.domain && (
                  <a
                    href={`https://${meeting.domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {meeting.domain} ↗
                  </a>
                )}
              </div>
            )}
          </div>
        </div>

        {meeting.attendees.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Attendees
            </h2>
            <div className="flex flex-wrap gap-2">
              {meeting.attendees.map((email, i) => (
                <Badge key={i} variant="outline" className="text-xs font-normal">
                  {email}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Intelligence Brief
          </h2>

          {meeting.brief_status === "pending" && <MeetingCardSkeleton />}

          {meeting.brief_status === "done" && meeting.brief && (
            <BriefContent brief={meeting.brief} />
          )}

          {meeting.brief_status === "no_company" && (
            <div className="rounded-lg border bg-muted/30 py-10 text-center text-sm text-muted-foreground">
              No company identified for this meeting — brief unavailable.
            </div>
          )}

          {meeting.brief_status === "error" && (
            <div className="rounded-lg border bg-destructive/5 py-10 text-center text-sm text-muted-foreground">
              Research failed — will retry on next calendar sync.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
