"use client";

import Link from 'next/link';
import { useCallback, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Playbook, PlaybookRunResponse, fetchPlaybooks, runPlaybook } from '@/lib/api';

type RunState = {
  status: 'idle' | 'loading' | 'success' | 'error';
  result?: PlaybookRunResponse;
  error?: string;
};

const defaultRunState: RunState = { status: 'idle' };

export function PlaybookList() {
  const { data, isLoading, isError, error, refetch } = useQuery<Playbook[], Error>({
    queryKey: ['playbooks'],
    queryFn: fetchPlaybooks,
    staleTime: 30_000,
  });

  const [runs, setRuns] = useState<Record<string, RunState>>({});

  const handleRun = useCallback(async (playbookId: string) => {
    setRuns((prev) => ({ ...prev, [playbookId]: { status: 'loading' } }));
    try {
      const response = await runPlaybook(playbookId);
      setRuns((prev) => ({ ...prev, [playbookId]: { status: 'success', result: response } }));
    } catch (err) {
      setRuns((prev) => ({
        ...prev,
        [playbookId]: { status: 'error', error: err instanceof Error ? err.message : String(err) },
      }));
    }
  }, []);

  const content = useMemo(() => {
    if (isLoading) {
      return <div className="rounded border border-slate-800 bg-slate-900/60 p-6">Loading playbooks…</div>;
    }

    if (isError) {
      return (
        <div className="space-y-3 rounded border border-rose-500/40 bg-rose-900/30 p-6 text-sm">
          <div className="font-semibold text-rose-200">Unable to load playbooks</div>
          <div className="text-rose-100/70">{error?.message}</div>
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

    if (!data || data.length === 0) {
      return (
        <div className="rounded border border-slate-800 bg-slate-900/60 p-6 text-slate-300">
          No playbooks available yet. Seed some Sigma/YARA hunts to get started.
        </div>
      );
    }

    return (
      <div className="grid gap-4 md:grid-cols-2">
        {data.map((playbook) => {
          const runState = runs[playbook.id] ?? defaultRunState;
          const runResult = runState.result?.result;
          return (
            <article
              key={playbook.id}
              className="flex flex-col justify-between rounded-lg border border-slate-800 bg-slate-900/60 p-6 shadow-lg shadow-slate-950/40"
            >
              <div className="space-y-3">
                <div>
                  <h2 className="text-xl font-semibold text-slate-50">{playbook.name}</h2>
                  <p className="text-sm text-slate-300">{playbook.description ?? 'No description provided.'}</p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs uppercase tracking-wide text-slate-400">
                  {playbook.tags.map((tag) => (
                    <span key={tag} className="rounded-full border border-slate-700 px-3 py-1">
                      {tag}
                    </span>
                  ))}
                  {playbook.tags.length === 0 && (
                    <span className="rounded-full border border-slate-700 px-3 py-1 text-slate-500">untagged</span>
                  )}
                </div>
                <div className="grid gap-1 text-xs text-slate-400">
                  <span>Rule: {playbook.rule_path}</span>
                  <span>Sample data: {playbook.data_path}</span>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-slate-800 pt-4">
                <button
                  type="button"
                  disabled={runState.status === 'loading'}
                  onClick={() => handleRun(playbook.id)}
                  className="rounded bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700"
                >
                  {runState.status === 'loading' ? 'Running…' : 'Quick Run'}
                </button>
                <Link
                  href={`/playbooks/${playbook.id}`}
                  className="text-sm font-semibold text-slate-200 underline-offset-4 hover:underline"
                >
                  View details
                </Link>
              </div>

              {runState.status === 'success' && runResult && (
                <div className="mt-4 rounded border border-sky-500/40 bg-sky-900/30 p-3 text-xs text-sky-100">
                  <div className="font-semibold">Last run summary</div>
                  <div>
                    Matches: {runResult.matched_count} / {runResult.total_records} records
                  </div>
                  <div className="text-[11px] text-sky-200/80">{runResult.execution_notes}</div>
                </div>
              )}

              {runState.status === 'error' && (
                <div className="mt-4 rounded border border-rose-500/40 bg-rose-900/30 p-3 text-xs text-rose-100">
                  <div className="font-semibold">Run failed</div>
                  <div>{runState.error}</div>
                </div>
              )}
            </article>
          );
        })}
      </div>
    );
  }, [data, error?.message, handleRun, isError, isLoading, refetch, runs]);

  return <section className="space-y-4">{content}</section>;
}
