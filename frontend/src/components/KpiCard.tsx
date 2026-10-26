type Props = { label: string; value: string; hint?: string; tone?: "neutral" | "good" | "bad" };

const TONES = { neutral: "text-slate-900", good: "text-emerald-700", bad: "text-rose-700" };

export function KpiCard({ label, value, hint, tone = "neutral" }: Props) {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${TONES[tone]}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
