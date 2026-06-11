interface SignOutPageProps {
  userName: string;
  userPicture: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function SignOutPage({ userName, userPicture, onConfirm, onCancel }: SignOutPageProps) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-sm mx-auto px-6">
        <div className="bg-card border rounded-xl p-8 shadow-sm text-center space-y-6">
          {/* Avatar */}
          <div className="flex flex-col items-center gap-3">
            <img
              src={userPicture}
              alt={userName}
              className="w-14 h-14 rounded-full border-2 border-border"
              referrerPolicy="no-referrer"
            />
            <div>
              <p className="font-semibold text-base">{userName}</p>
              <p className="text-sm text-muted-foreground mt-0.5">Are you sure you want to sign out?</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2.5">
            <button
              onClick={onConfirm}
              className="w-full py-2.5 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors text-sm font-medium"
            >
              Sign out
            </button>
            <button
              onClick={onCancel}
              className="w-full py-2.5 rounded-lg border hover:bg-muted transition-colors text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>

        <p className="text-xs text-center text-muted-foreground mt-6">
          Meeting Intel · AI-powered research
        </p>
      </div>
    </div>
  );
}
