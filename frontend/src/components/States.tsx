export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div
      role="status"
      className="animate-pulse rounded-xl bg-white p-6 text-sm text-slate-500 shadow-sm ring-1 ring-slate-200"
    >
      {label}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : "Something went wrong";
  return (
    <div
      role="alert"
      className="rounded-xl bg-rose-50 p-6 text-sm text-rose-800 ring-1 ring-rose-200"
    >
      <p className="font-medium">Couldn't load this view</p>
      <p className="mt-1">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md bg-white px-3 py-1.5 font-medium ring-1 ring-rose-300 hover:bg-rose-100"
        >
          Retry
        </button>
      )}
    </div>
  );
}
