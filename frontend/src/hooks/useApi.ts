import { useState, useEffect, useCallback } from 'react';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApi<T>(fn: () => Promise<T>, deps: any[] = []): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Request failed');
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => { load(); }, [load]);
  return { data, loading, error, refetch: load };
}
