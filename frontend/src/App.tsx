import type { ReactNode } from "react";
import type { AuctionInfo, Meta } from "./api/client";
import { useMeta } from "./api/hooks";
import { AuctionSelect } from "./components/AuctionSelect";
import { ErrorState, Loading } from "./components/States";
import { AccuracyView } from "./features/accuracy/AccuracyView";
import { DeliveryDayView } from "./features/delivery-day/DeliveryDayView";
import { MethodPanel } from "./features/method/MethodPanel";
import { setSearchParams, useSearchParam } from "./lib/url-state";

// Tabs are added as views are built; the first entry is the landing view.
const TABS = [
  { id: "day", label: "Delivery day" },
  { id: "accuracy", label: "Accuracy" },
  { id: "method", label: "Method & data" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const meta = useMeta();
  const [tabParam] = useSearchParam("tab");
  const [auctionParam, setAuction] = useSearchParam("auction");

  if (meta.isPending) {
    return (
      <Layout>
        <Loading label="Loading WindDesk…" />
      </Layout>
    );
  }
  if (meta.isError) {
    return (
      <Layout>
        <ErrorState error={meta.error} onRetry={() => void meta.refetch()} />
      </Layout>
    );
  }

  const tab: TabId = TABS.find((t) => t.id === tabParam)?.id ?? TABS[0].id;
  const auction = resolveAuction(meta.data, auctionParam);

  return (
    <Layout
      controls={
        <AuctionSelect
          auctions={meta.data.auctions}
          value={auction.id}
          onChange={(id) => setAuction(id)}
        />
      }
      nav={<TabNav current={tab} />}
    >
      {tab === "day" && <DeliveryDayView meta={meta.data} auction={auction} />}
      {tab === "accuracy" && (
        <AccuracyView
          auction={auction}
          onOpenDay={(date) => setSearchParams({ tab: "day", date })}
        />
      )}
      {tab === "method" && <MethodPanel meta={meta.data} />}
    </Layout>
  );
}

function resolveAuction(meta: Meta, id: string | null): AuctionInfo {
  const { auctions } = meta;
  return (
    auctions.find((a) => a.id === id) ??
    auctions.find((a) => a.id === meta.default_auction) ??
    auctions[0]!
  );
}

function TabNav({ current }: { current: TabId }) {
  return (
    <nav aria-label="Views" className="-mb-px flex gap-1 overflow-x-auto">
      {TABS.map((t) => (
        <button
          key={t.id}
          type="button"
          aria-current={t.id === current ? "page" : undefined}
          onClick={() => setSearchParams({ tab: t.id })}
          className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium ${
            t.id === current
              ? "border-blue-600 text-blue-700"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}

type LayoutProps = { controls?: ReactNode; nav?: ReactNode; children: ReactNode };

function Layout({ controls, nav, children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <img src="/favicon.svg" alt="" className="h-8 w-8" />
            <div>
              <h1 className="text-lg font-semibold tracking-tight">WindDesk</h1>
              <p className="text-xs text-slate-500">
                GB day-ahead wind forecast intelligence · pilot: purchase decisions made in January
                2026
              </p>
            </div>
          </div>
          {controls}
        </div>
        {nav && <div className="mx-auto max-w-7xl px-4 sm:px-6">{nav}</div>}
      </header>
      <main className="mx-auto max-w-7xl space-y-4 px-4 py-6 sm:px-6">{children}</main>
      <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs text-slate-500 sm:px-6">
        Contains BMRS data © Elexon Limited copyright and database right 2026. All times UK local.
      </footer>
    </div>
  );
}
