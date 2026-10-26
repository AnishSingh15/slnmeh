import type { ReactNode } from "react";

type Props = { title: string; subtitle?: string; actions?: ReactNode; children: ReactNode };

export function Card({ title, subtitle, actions, children }: Props) {
  return (
    <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200 sm:p-5">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
