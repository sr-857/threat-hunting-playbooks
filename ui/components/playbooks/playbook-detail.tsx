"use client";

import Link from 'next/link';
import { useCallback, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import {
  Playbook,
  PlaybookRunResponse,
  fetchPlaybook,
  runPlaybook,
} from '@/lib/api';

interface PlaybookDetailProps {
  playbookId: string;
}

type RunState = {
  status: 'idle' | 'loading' | 'success' | 'error';
  result?: PlaybookRunResponse;
  error?: string;
};

export function PlaybookDetail({ playbookId }: PlaybookDetailProps) {
  const { data, isLoading, isError, error, refetch } = useQuery<Playbook, Error>({
    queryKey: ['playbook', playbookId],
    queryFn: () => fetchPlaybook(playbookId),
    staleTime: 30_000,
  });

  const [runState, setRunState] = useState<RunState>({ status: 'idle' });

  const handleRun = useCallback(async () => {
    setRunState({ status: 'loading' });
    try {
      const response = await runPlaybook(playbookId);
      setRunState({ status: 'success', result: response });
    } catch (err) {
      setRunState({
        status: 'error',
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }, [playbookId]);

  const body = useMemo(() => {
    if (isLoading) {
      return <div className="rounded border border-slate-800 bg-slate-900/60 p-6">Loading…</div>;
    }

    if (isError || !data) {
      return (
        <div className="space-y-3 rounded border border-rose-500/40 bg-rose-900/30 p-6 text-sm">
          <div className="font-semibold text-rose-200">Unable to load playbook</div>
          <div className="text-rose-100/70">{error?.message ?? 'Unknown error'}</div>
          <button
            type="button"
            onClick={() => refetch()}
            className="rounded bg-rose-500/90 px-3 py-2 text-xs font-semibold text-white hover:bg-rose-500"
          >
            Retry
          </button>
        </div>
      );
    }

    const matches = runState.result?.result.matches ?? [];

    return (
      <div className="space-y-6">
        <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 shadow-lg shadow-slate-950/40">
          <div className="flex flex-col gap-3">
            <div>
              <h1 className="text-3xl font-semibold text-slate-50">{data.name}</h1>
              <p className="text-slate-300">{data.description ?? 'No description available.'}</p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs uppercase tracking-wide text-slate-400">
              {data.tags.map((tag) => (
                <span key={tag} className="rounded-full border border-slate-700 px-3 py-1">
                  {tag}
                </span>
              ))}
              {data.tags.length === 0 && (
                <span className="rounded-full border border-slate-700 px-3 py-1 text-slate-500">untagged</span>
              )}
            </div>
            <dl className="grid gap-2 text-sm text-slate-300 md:grid-cols-2">
              <div>
                <dt className="font-semibold text-slate-200">Rule path</dt>
                <dd className="text-slate-400">{data.rule_path}</dd>
              </div>
              <div>
                <dt className="font-semibold text-slate-200">Sample dataset</dt>
                <dd className="text-slate-400">{data.data_path}</dd>
              </div>
              <div>
                <dt className="font-semibold text-slate-200">Created</dt>
                <dd className="text-slate-400">{new Date(data.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="font-semibold text-slate-200">Updated</dt>
                <dd className="text-slate-400">{new Date(data.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>
          <div className="mt-6 flex items-center justify-between border-t border-slate-800 pt-4">
            <button
              type="button"
              onClick={handleRun}
              disabled={runState.status === 'loading'}
              className="rounded bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700"
            >
              {runState.status === 'loading' ? 'Running…' : 'Run playbook'}
            </button>
            <div className="text-xs text-slate-500">Outputs stored locally</div>
          </div>

          {runState.status === 'success' && runState.result && (
            <div className="mt-6 space-y-3 rounded border border-sky-500/40 bg-sky-900/30 p-4 text-sm text-sky-100">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold">Execution summary</div>
                  <div>
                    Matches: {runState.result.result.matched_count} / {runState.result.result.total_records}
                  </div>
                </div>
                <div className="text-xs text-sky-200/80">{runState.result.result.execution_notes}</div>
              </div>
              <div className="max-h-64 overflow-auto rounded border border-sky-500/20">
                <table className="w-full table-auto text-xs">
                  <thead className="bg-sky-950/60 text-sky-200">
                    <tr>
                      <th className="px-3 py-2 text-left">Matched</th>
                      <th className="px-3 py-2 text-left">Reason</th>
                      <th className="px-3 py-2 text-left">Record</th>
                    </tr>
                  </thead>
                  <tbody>
                    {matches.map((match, index) => (
                      <tr key={`${match.matched}-${index}`} className="odd:bg-sky-950/30">
                        <td className="px-3 py-2 font-semibold">
                          {match.matched ? (
                            <span className="text-green-400">Yes</span>
                          ) : (
                            <span className="text-slate-400">No</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-slate-200">{match.reason ?? '—'}</td>
                        <td className="px-3 py-2 text-slate-200">
                          <pre className="whitespace-pre-wrap text-[11px] text-slate-300">
                            {JSON.stringify(match.record, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    ))}
                    {matches.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-3 py-4 text-center text-sky-200/70">
                          No execution data yet. Run the playbook to generate results.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {runState.status === 'error' && (
            <div className="mt-6 rounded border border-rose-500/40 bg-rose-900/30 p-4 text-sm text-rose-100">
              <div className="font-semibold">Execution failed</div>
              <div>{runState.error}</div>
            </div>
          )}
        </section>
      </div>
    );
  }, [data, error?.message, handleRun, isError, isLoading, refetch, runState]);

  return (
    <div className="space-y-4">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-300 hover:text-slate-100">
        ← Back to playbooks
      </Link>
      {body}
    </div>
  );
}
