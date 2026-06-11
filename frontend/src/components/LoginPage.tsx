import { useEffect, useRef, useState } from "react";

interface LoginPageProps {
  onRender: (el: HTMLElement | null) => void;
  error: string | null;
  loading: boolean;
}

export function LoginPage({ onRender, error, loading }: LoginPageProps) {
  const btnRef = useRef<HTMLDivElement>(null);
  const [gsiLoaded, setGsiLoaded] = useState(false);

  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 20;

    const tryRender = () => {
      attempts++;
      if ((window as any).google?.accounts?.id) {
        onRender(btnRef.current);
        setGsiLoaded(true);
      } else if (attempts < maxAttempts) {
        setTimeout(tryRender, 300);
      }
    };

    setTimeout(tryRender, 200);
  }, [onRender]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-sm mx-auto px-6">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 mb-4">
            <svg className="w-7 h-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Meeting Intel</h1>
          <p className="text-sm text-muted-foreground mt-1">AI-powered research for every meeting</p>
        </div>

        <div className="bg-card border rounded-xl p-8 shadow-sm space-y-6">
          <div className="text-center">
            <h2 className="text-base font-semibold">Sign in to continue</h2>
            <p className="text-xs text-muted-foreground mt-1">Access restricted to authorised accounts</p>
          </div>

          {error && (
            <div className="bg-destructive/10 text-destructive text-sm rounded-lg px-4 py-3 text-center">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-2">
              <div className="w-5 h-5 border-2 border-primary/40 border-t-primary rounded-full animate-spin" />
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              {/* GSI renders the official Google button here */}
              <div ref={btnRef} />

              {/* Fallback only shown if GSI did not load */}
              {!gsiLoaded && (
                <button
                  onClick={() => (window as any).google?.accounts?.id?.prompt()}
                  className="flex items-center gap-3 px-5 py-2.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700 shadow-sm w-full justify-center"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Sign in with Google
                </button>
              )}
            </div>
          )}
        </div>

        <p className="text-xs text-center text-muted-foreground mt-6">Only approved accounts can access this app</p>
      </div>
    </div>
  );
}
