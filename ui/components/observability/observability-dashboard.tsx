"use client";

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { fetchTelemetryAlerts, fetchTelemetryEvents, TelemetryAlert, TelemetryEvent } from '@/lib/api';

const EMPTY_STATE = 'No data yet. Hunts will appear here after they execute.';

function useTelemetry(limit: number) {
  const [eventLimit, setEventLimit] = useState(limit);
  const [alertLimit, setAlertLimit] = useState(limit);

  const eventsQuery = useQuery<TelemetryEvent[], Error>({
    queryKey: ['telemetry', 'events', eventLimit],
    queryFn: () => fetchTelemetryEvents(eventLimit),
    refetchInterval: 60_000,
  });

  const alertsQuery = useQuery<TelemetryAlert[], Error>({
    queryKey: ['telemetry', 'alerts', alertLimit],
    queryFn: () => fetchTelemetryAlerts(alertLimit),
    refetchInterval: 60_000,
  });

  return { eventsQuery, alertsQuery, eventLimit, alertLimit, setEventLimit, setAlertLimit };
}

function formatTimestamp(value: string) {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function ObservabilityDashboard({ defaultLimit = 50 }: { defaultLimit?: number }) {
  const { eventsQuery, alertsQuery, eventLimit, alertLimit, setEventLimit, setAlertLimit } = useTelemetry(defaultLimit);

  const alerts = alertsQuery.data ?? [];
  const events = eventsQuery.data ?? [];

  const aggregateStats = useMemo(() => {
    const sourceEvents = eventsQuery.data ?? [];
    if (!sourceEvents.length) {
      return null;
    }
    const huntsByPlaybook = new Map<string, { total: number; matched: number }>();
    sourceEvents.forEach((event) => {
      if (!event.playbook_id) {
        return;
      }
      const current = huntsByPlaybook.get(event.playbook_id) ?? { total: 0, matched: 0 };
      current.total += 1;
      if ((event.confidence ?? 0) > 0) {
        current.matched += 1;
      }
      huntsByPlaybook.set(event.playbook_id, current);
    });
    return Array.from(huntsByPlaybook.entries()).map(([playbookId, stats]) => ({
      playbookId,
      ...stats,
    }));
  }, [eventsQuery.data]);

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">Alerts</h2>
            <p className="text-sm text-slate-400">Hunts exceeding the configured confidence threshold.</p>
          </div>
          <label className="text-xs text-slate-400">
            Limit
            <select
              value={alertLimit}
              onChange={(event) => setAlertLimit(Number(event.target.value))}
              className="ml-2 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-slate-100"
            >
              {[25, 50, 100].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </header>
        {alertsQuery.isLoading ? (
          <div className="rounded border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-300">Loading alerts…</div>
        ) : alertsQuery.isError ? (
          <div className="rounded border border-rose-500/40 bg-rose-900/30 p-6 text-sm text-rose-100">
            Failed to load alerts: {alertsQuery.error?.message}
          </div>
        ) : alerts.length === 0 ? (
          <div className="rounded border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-300">{EMPTY_STATE}</div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <article
                key={`${alert.timestamp}-${alert.playbook_id}`}
                className="rounded border border-sky-500/40 bg-sky-900/30 p-4"
              >
                <div className="flex justify-between text-sm text-sky-100">
                  <span className="font-semibold">Playbook {alert.playbook_id}</span>
                  <span>{formatTimestamp(alert.timestamp)}</span>
                </div>
                <dl className="mt-2 grid gap-2 text-xs text-sky-200 md:grid-cols-3">
                  <div>
                    <dt className="uppercase tracking-wide">Confidence</dt>
                    <dd>
                      {(alert.confidence * 100).toFixed(1)}% (threshold {(alert.threshold * 100).toFixed(1)}%)
                    </dd>
                  </div>
                  <div>
                    <dt className="uppercase tracking-wide">Trigger</dt>
                    <dd>{alert.trigger ?? 'Unknown'}</dd>
                  </div>
                  <div>
                    <dt className="uppercase tracking-wide">Schedule</dt>
                    <dd>{alert.schedule_id ?? '—'}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">Recent Hunts</h2>
            <p className="text-sm text-slate-400">Combined view of manual and scheduled executions.</p>
          </div>
          <label className="text-xs text-slate-400">
            Limit
            <select
              value={eventLimit}
              onChange={(event) => setEventLimit(Number(event.target.value))}
              className="ml-2 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-slate-100"
            >
              {[25, 50, 100].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </header>
        {eventsQuery.isLoading ? (
          <div className="rounded border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-300">Loading hunts…</div>
        ) : eventsQuery.isError ? (
          <div className="rounded border border-rose-500/40 bg-rose-900/30 p-6 text-sm text-rose-100">
            Failed to load hunts: {eventsQuery.error?.message}
          </div>
        ) : events.length === 0 ? (
          <div className="rounded border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-300">{EMPTY_STATE}</div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <article key={`${event.timestamp}-${event.playbook_id}`} className="rounded border border-slate-800 bg-slate-900/60 p-4">
                <div className="flex justify-between text-sm text-slate-200">
                  <span className="font-semibold">Playbook {event.playbook_id}</span>
                  <span>{formatTimestamp(event.timestamp)}</span>
                </div>
                <dl className="mt-2 grid gap-2 text-xs text-slate-300 md:grid-cols-4">
                  <div>
                    <dt className="uppercase tracking-wide">Trigger</dt>
                    <dd>{event.trigger ?? 'manual'}</dd>
                  </div>
                  <div>
                    <dt className="uppercase tracking-wide">Matched / Total</dt>
                    <dd>
                      {event.matched_count ?? '—'} / {event.total_records ?? '—'} ({((event.confidence ?? 0) * 100).toFixed(1)}%)
                    </dd>
                  </div>
                  <div>
                    <dt className="uppercase tracking-wide">Schedule</dt>
                    <dd>{event.schedule_id ?? '—'}</dd>
                  </div>
                  <div>
                    <dt className="uppercase tracking-wide">Notes</dt>
                    <dd>{event.notes ?? '—'}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        )}
      </section>

      {aggregateStats && aggregateStats.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-100">Playbook Summary</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {aggregateStats.map((item) => (
              <div key={item.playbookId} className="rounded border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-200">
                <div className="font-semibold text-slate-50">Playbook {item.playbookId}</div>
                <div className="mt-1 text-xs text-slate-400">
                  {item.matched} positive hunts out of {item.total} total executions
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
