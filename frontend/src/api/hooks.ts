import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api, type AuctionId } from "./client";

export const useMeta = () => useQuery({ queryKey: ["meta"], queryFn: api.meta });

export const useDeliveryDay = (date: string | undefined, auction: AuctionId) =>
  useQuery({
    queryKey: ["delivery-day", date, auction],
    queryFn: () => api.deliveryDay(date!, auction),
    enabled: date !== undefined,
    placeholderData: keepPreviousData,
  });

export const useAccuracy = (auction: AuctionId) =>
  useQuery({
    queryKey: ["accuracy", auction],
    queryFn: () => api.accuracy(auction),
    placeholderData: keepPreviousData,
  });

export const useLeadTime = (start: string, end: string, hours: number) =>
  useQuery({
    queryKey: ["lead-time", start, end, hours],
    queryFn: () => api.leadTime(start, end, hours),
    placeholderData: keepPreviousData,
  });
