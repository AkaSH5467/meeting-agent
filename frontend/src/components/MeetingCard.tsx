import { Badge } from "@/components/ui/badge";
import type { Meeting } from "../types";
import { clsx } from "clsx";

function formatIST(date: Date): string {
  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

const statusConfig: Record<string, { label: string; className: string }> = {
  pending:    { label: "Researching…", className: "bg-yellow-100 text-yellow-800" },
  done:       { label: "Ready",        className: "bg-green-100 text-green-800" },
  no_company: { label: "No company",   className: "bg-gray-100 text-gray-700" },
  error:      { label: "Error",        className: "bg-red-100 text-red-700" },
};

function getMeetingStatus(meeting: Meeting): { label: string; className: string } {
  // Compare raw UTC timestamps — never use toZonedTime for comparisons
  const now = new Date();
  const start = new Date(meeting.start_time.endsWith("Z") ? meeting.start_time : meeting.start_time + "Z");
  const end = new Date(meeting.end_time.endsWith("Z") ? meeting.end_time : meeting.end_time + "Z");

  if (now >= start && now <= end) {
    return { label: "In progress", className: "bg-blue-100 text-blue-800" };
  }
  if (now > end) {
    return { label: "Done", className: "bg-gray-100 text-gray-600" };
  }
  return statusConfig[meeting.brief_status] ?? { label: meeting.brief_status, className: "bg-gray-100 text-gray-600" };
}

interface MeetingCardProps {
  meeting: Meeting;
  onDelete: (id: string) => void;
}

function toUTC(s: string): Date {
  // DB stores naive UTC — append Z so browser doesn't misread as local time
  return new Date(s.endsWith("Z") ? s : s + "Z");
}

export function MeetingCard({ meeting, onDelete }: MeetingCardProps) {
  const startTime = toUTC(meeting.start_time);
  const status = getMeetingStatus(meeting);

  const openDetail = () => {
    window.open(
      `${window.location.origin}${window.location.pathname}#meeting/${meeting.id}`,
      "_blank"
    );
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // don't open the detail page
    onDelete(meeting.id);
  };

  return (
    <div
      className={clsx(
        "flex items-center justify-between px-4 py-3 rounded-lg border bg-card",
        "cursor-pointer hover:bg-muted/50 hover:border-primary/40 transition-all group"
      )}
      onClick={openDetail}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && openDetail()}
      aria-label={`Open brief for ${meeting.title}`}
    >
      {/* Left: title + time */}
      <div className="min-w-0 flex-1 mr-4">
        <p className="font-medium text-sm truncate group-hover:text-primary transition-colors">
          {meeting.title}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {formatIST(startTime)}
        </p>
      </div>

      {/* Right: status + open icon + delete */}
      <div className="flex items-center gap-2 shrink-0">
        <Badge className={clsx(status.className, "text-xs font-normal")}>
          {status.label}
        </Badge>
        <svg
          className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-primary/60 transition-colors"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>

        {/* Delete button — only visible on hover */}
        <button
          onClick={handleDelete}
          aria-label={`Dismiss ${meeting.title}`}
          className={clsx(
            "p-1 rounded hover:bg-destructive/10 hover:text-destructive",
            "text-muted-foreground/30 transition-all",
            "opacity-0 group-hover:opacity-100"
          )}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
