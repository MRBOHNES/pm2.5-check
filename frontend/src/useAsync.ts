import { useEffect, useState } from "react";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "ok"; data: T };

/**
 * Run `load` whenever `key` changes; cancels the previous request.
 * "loading" is derived (no result stored for the current key yet), so no setState
 * is needed at the start of the effect.
 */
export function useAsync<T>(load: (signal: AbortSignal) => Promise<T>, key: string): AsyncState<T> {
  const [result, setResult] = useState<{ key: string; state: Exclude<AsyncState<T>, { status: "loading" }> } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then(
      (data) => setResult({ key, state: { status: "ok", data } }),
      (error: Error) => {
        if (!controller.signal.aborted) setResult({ key, state: { status: "error", error } });
      },
    );
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` stands in for `load`
  }, [key]);
  return result && result.key === key ? result.state : { status: "loading" };
}
