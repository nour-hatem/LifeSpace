import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "../../shared/api/client";

type HealthResponse = {
  status: string;
};

export function ApiStatus() {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<HealthResponse>("/api/health"),
    retry: false,
  });

  if (query.isPending) {
    return <p>API status: checking</p>;
  }
  if (query.isError) {
    return <p>API status: unreachable</p>;
  }
  return <p>API status: {query.data.status}</p>;
}
