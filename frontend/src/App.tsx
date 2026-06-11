import { useState, useEffect } from "react";
import { useLiveMeetings } from "./hooks/useLiveMeetings";
import { useAuth } from "./hooks/useAuth";
import { MeetingCard } from "./components/MeetingCard";
import { MeetingDetailPage } from "./components/MeetingDetailPage";
import { LoginPage } from "./components/LoginPage";
import { SignOutPage } from "./components/SignOutPage";
import { clsx } from "clsx";

const EXPIRY_HOURS = 12;

function useHashRoute() {
  const [meetingId, setMeetingId] = useState<string | null>(() => {
    const match = window.location.hash.match(/^#meeting\/(.+)$/);
    return match ? match[1] : null;
  });

  useEffect(() => {
    const onHashChange = () => {
      const match = window.location.hash.match(/^#meeting\/(.+)$/);
      setMeetingId(match ? match[1] : null);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const goBack = () => { window.location.hash = ""; };
  return { meetingId, goBack };
}

function Dashboard({ onSignOutClick }: { onSignOutClick: () => void }) {
  const { meetings, isConnected } = useLiveMeetings();
  const { user } = useAuth();
  const [dismissed, setDismissed] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem("dismissed_meetings");
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  const handleDelete = (id: string) => {
    setDismissed((prev) => {
      const next = new Set(prev).add(id);
      localStorage.setItem("dismissed_meetings", JSON.stringify([...next]));
      return next;
    });
  };

  // DB stores naive UTC — append Z so browser parses correctly
  const toUTC = (s: string) => new Date(s.endsWith("Z") ? s : s + "Z");

  // Filter out meetings that are older than EXPIRY_HOURS after their scheduled start
  const now = new Date();
  const visibleMeetings = meetings.filter((m) => {
    if (dismissed.has(m.id)) return false;
    const start = toUTC(m.start_time);
    const expiresAt = new Date(start.getTime() + EXPIRY_HOURS * 60 * 60 * 1000);
    return now < expiresAt;
  });

  // Split into upcoming/today vs past (within expiry window)
  const upcomingMeetings = visibleMeetings.filter((m) => toUTC(m.end_time) > now);
  const recentMeetings = visibleMeetings.filter((m) => toUTC(m.end_time) <= now);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-base tracking-tight">Meeting Intel</span>
            <span className={clsx("w-1.5 h-1.5 rounded-full", isConnected ? "bg-green-500" : "bg-gray-400")} />
          </div>
          {user && (
            <button
              onClick={onSignOutClick}
              className="flex items-center gap-2 hover:opacity-75 transition-opacity"
              aria-label="Sign out"
            >
              <img
                src={user.picture}
                alt={user.name}
                className="w-7 h-7 rounded-full border"
                referrerPolicy="no-referrer"
              />
            </button>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {upcomingMeetings.length > 0 && (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">Upcoming</h2>
            <div className="space-y-2">
              {upcomingMeetings.map((meeting) => (
                <MeetingCard key={meeting.id} meeting={meeting} onDelete={handleDelete} />
              ))}
            </div>
          </section>
        )}

        {recentMeetings.length > 0 && (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">Recent</h2>
            <div className="space-y-2">
              {recentMeetings.map((meeting) => (
                <MeetingCard key={meeting.id} meeting={meeting} onDelete={handleDelete} />
              ))}
            </div>
          </section>
        )}

        {visibleMeetings.length === 0 && (
          <div className="text-center py-16 text-muted-foreground text-sm">
            No meetings in the last {EXPIRY_HOURS} hours or upcoming
          </div>
        )}
      </main>
    </div>
  );
}

function App() {
  const { user, error, loading, signOut, renderGoogleButton } = useAuth();
  const { meetingId, goBack } = useHashRoute();
  const [showSignOut, setShowSignOut] = useState(false);

  if (!user) {
    return <LoginPage onRender={renderGoogleButton} error={error} loading={loading} />;
  }

  if (showSignOut) {
    return (
      <SignOutPage
        userName={user.name}
        userPicture={user.picture}
        onConfirm={() => { setShowSignOut(false); signOut(); }}
        onCancel={() => setShowSignOut(false)}
      />
    );
  }

  if (meetingId) {
    return <MeetingDetailPage meetingId={meetingId} onBack={goBack} />;
  }

  return <Dashboard onSignOutClick={() => setShowSignOut(true)} />;
}

export default App;
