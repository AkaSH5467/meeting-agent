import { useState, useEffect, useCallback } from "react";
import type { GoogleUser } from "../types";

// ── CONFIGURE: add allowed emails here ──────────────────────────────────────
const ALLOWED_EMAILS = [
  "acm8769@gmail.com",
  "acm7970309988@gmail.com",
];
// ─────────────────────────────────────────────────────────────────────────────

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string;
const STORAGE_KEY = "meeting_intel_user";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: object) => void;
          prompt: () => void;
          renderButton: (el: HTMLElement, config: object) => void;
          revoke: (email: string, done: () => void) => void;
        };
      };
    };
  }
}

export function useAuth() {
  const [user, setUser] = useState<GoogleUser | null>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      return stored ? (JSON.parse(stored) as GoogleUser) : null;
    } catch {
      return null;
    }
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [gsiReady, setGsiReady] = useState(false);

  const handleCredential = useCallback((credentialResponse: { credential: string }) => {
    setLoading(true);
    setError(null);
    try {
      const payload = JSON.parse(atob(credentialResponse.credential.split(".")[1]));
      const googleUser: GoogleUser = {
        email: payload.email,
        name: payload.name,
        picture: payload.picture,
        sub: payload.sub,
      };

      if (!ALLOWED_EMAILS.includes(googleUser.email)) {
        setError(`Access denied. ${googleUser.email} is not on the allowed list.`);
        setLoading(false);
        return;
      }

      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(googleUser));
      setUser(googleUser);
    } catch {
      setError("Failed to process sign-in. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) return;

    const initGoogle = () => {
      window.google?.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: handleCredential,
        auto_select: false,
      });
      setGsiReady(true);
    };

    if (window.google?.accounts?.id) {
      initGoogle();
      return;
    }

    if (document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
      const poll = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(poll);
          initGoogle();
        }
      }, 100);
      return () => clearInterval(poll);
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = initGoogle;
    document.head.appendChild(script);
  }, [user, handleCredential]);

  const signOut = useCallback(() => {
    if (user) {
      window.google?.accounts.id.revoke(user.email, () => {});
    }
    sessionStorage.removeItem(STORAGE_KEY);
    setUser(null);
    setError(null);
  }, [user]);

  const renderGoogleButton = useCallback((el: HTMLElement | null) => {
    if (!el || !window.google?.accounts?.id) return;
    window.google.accounts.id.renderButton(el, {
      type: "standard",
      theme: "outline",
      size: "large",
      text: "signin_with",
      shape: "rectangular",
      logo_alignment: "left",
      width: 280,
    });
  }, []);

  return { user, error, loading, gsiReady, signOut, renderGoogleButton };
}