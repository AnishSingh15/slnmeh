import type { AuctionId, AuctionInfo } from "../api/client";

type Props = { auctions: AuctionInfo[]; value: AuctionId; onChange: (id: AuctionId) => void };

export function AuctionSelect({ auctions, value, onChange }: Props) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-slate-500">Auction</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as AuctionId)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm shadow-sm"
      >
        {auctions.map((auction) => (
          <option key={auction.id} value={auction.id}>
            {auction.label} · gate closes {auction.gate_closure}
          </option>
        ))}
      </select>
    </label>
  );
}
