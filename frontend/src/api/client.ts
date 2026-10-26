import type { components } from "./schema";

type Schemas = components["schemas"];
export type Meta = Schemas["MetaResponse"];
export type AuctionInfo = Schemas["AuctionInfo"];
export type AuctionId = AuctionInfo["id"];
export type DeliveryDay = Schemas["DeliveryDayResponse"];
export type HourRow = Schemas["HourRow"];
export type Accuracy = Schemas["AccuracyResponse"];
export type ErrorSummary = Schemas["ErrorSummaryModel"];
export type GroupStat = Schemas["GroupStat"];
export type LeadTime = Schemas["LeadTimeResponse"];

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function getJson<T>(path: string, params: Record<string, string | number> = {}): Promise<T> {
  const query = new URLSearchParams(
    Object.entries(params).map(([key, value]) => [key, String(value)]),
  ).toString();
  const response = await fetch(query ? `${path}?${query}` : path);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail =
      typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  meta: () => getJson<Meta>("/api/meta"),
  deliveryDay: (date: string, auction: AuctionId) =>
    getJson<DeliveryDay>("/api/delivery-day", { date, auction }),
  accuracy: (auction: AuctionId) => getJson<Accuracy>("/api/accuracy", { auction }),
  leadTime: (start: string, end: string, hours: number) =>
    getJson<LeadTime>("/api/lead-time", { start, end, hours }),
};
