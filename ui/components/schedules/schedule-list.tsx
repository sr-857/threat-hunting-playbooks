"use client";

import { useCallback, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  CreateScheduleInput,
  HuntSchedule,
  Playbook,
  UpdateScheduleInput,
  createSchedule,
  deleteSchedule,
  fetchPlaybooks,
  fetchSchedules,
  runSchedule,
  updateSchedule,
} from '@/lib/api';

interface ScheduleRunState {
  status: 'idle' | 'loading' | 'success' | 'error';
  error?: string;
}

interface FormState {
  name: string;
  description: string;
  playbook_id: string;
  cron_expression: string;
  enabled: boolean;
}

const DEFAULT_FORM_STATE: FormState = {
  name: '',
  description: '',
  playbook_id: '',
  cron_expression: '* * * * *',
  enabled: true,
};

export function ScheduleList() {
  const queryClient = useQueryClient();

  const {
    data: schedules,
    isLoading: schedulesLoading,
    error: schedulesError,
  } = useQuery<HuntSchedule[], Error>({
    queryKey: ['schedules'],
    queryFn: fetchSchedules,
    staleTime: 15_000,
  });

  const {
    data: playbooks,
    isLoading: playbooksLoading,
    error: playbooksError,
  } = useQuery<Playbook[], Error>({
    queryKey: ['playbooks'],
    queryFn: fetchPlaybooks,
    staleTime: 300_000,
  });

  const [formState, setFormState] = useState<FormState>({ ...DEFAULT_FORM_STATE });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<Record<string, ScheduleRunState>>({});

  const createMutation = useMutation<HuntSchedule, Error, CreateScheduleInput>({
    mutationFn: async (input: CreateScheduleInput) => createSchedule(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setFormState({ ...DEFAULT_FORM_STATE });
      setEditingId(null);
      setRunStatus({});
    },
  });

  const updateMutation = useMutation<HuntSchedule, Error, { id: string; data: UpdateScheduleInput }>({
    mutationFn: async ({ id, data }) => updateSchedule(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setEditingId(null);
      setFormState({ ...DEFAULT_FORM_STATE });
    },
  });

  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: async (scheduleId: string) => deleteSchedule(scheduleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });

  const runMutation = useMutation<{ status: string }, Error, string>({
    mutationFn: async (scheduleId: string) => runSchedule(scheduleId),
    onMutate: async (scheduleId: string) => {
      setRunStatus((previous: Record<string, ScheduleRunState>) => ({
        ...previous,
        [scheduleId]: { status: 'loading' },
      }));
    },
    onError: (error: unknown, scheduleId: string) => {
      setRunStatus((previous: Record<string, ScheduleRunState>) => ({
        ...previous,
        [scheduleId]: {
          status: 'error',
          error: error instanceof Error ? error.message : String(error),
        },
      }));
    },
    onSuccess: (_data, scheduleId: string) => {
      setRunStatus((previous: Record<string, ScheduleRunState>) => ({
        ...previous,
        [scheduleId]: { status: 'success' },
      }));
      void queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });

  const handleInputChange = useCallback(<K extends keyof FormState>(key: K, value: FormState[K]) => {
    setFormState((previous: FormState) => ({ ...previous, [key]: value }));
  }, []);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!formState.playbook_id) {
        return;
      }

      if (editingId) {
        const payload: UpdateScheduleInput = {
          name: formState.name,
          description: formState.description || undefined,
          cron_expression: formState.cron_expression,
          enabled: formState.enabled,
        };
        await updateMutation.mutateAsync({ id: editingId, data: payload });
      } else {
        const payload: CreateScheduleInput = {
          name: formState.name,
          description: formState.description || undefined,
          playbook_id: formState.playbook_id,
          cron_expression: formState.cron_expression,
          enabled: formState.enabled,
        };
        await createMutation.mutateAsync(payload);
      }
    },
    [createMutation, editingId, formState, updateMutation],
  );

  const handleEdit = useCallback((schedule: HuntSchedule) => {
    setEditingId(schedule.id);
    setFormState({
      name: schedule.name,
      description: schedule.description ?? '',
      playbook_id: schedule.playbook_id,
      cron_expression: schedule.cron_expression,
      enabled: schedule.enabled,
    });
  }, []);

  const handleCancelEdit = useCallback(() => {
    setEditingId(null);
    setFormState({ ...DEFAULT_FORM_STATE });
  }, []);

  const handleDelete = useCallback(
    async (scheduleId: string) => {
      if (window.confirm('Delete this schedule?')) {
        await deleteMutation.mutateAsync(scheduleId);
      }
    },
    [deleteMutation],
  );

  const handleRun = useCallback(
    async (scheduleId: string) => {
      setRunStatus((previous: Record<string, ScheduleRunState>) => ({
        ...previous,
        [scheduleId]: { status: 'loading' },
      }));
      await runMutation.mutateAsync(scheduleId);
    },
    [runMutation],
  );

  const scheduleCards = useMemo(() => {
    if (schedulesLoading) {
      return <div className="rounded border border-slate-800 bg-slate-900/60 p-4">Loading schedules…</div>;
    }

    if (schedulesError) {
      return (
        <div className="rounded border border-rose-500/40 bg-rose-900/30 p-4 text-sm text-rose-100">
          Failed to load schedules: {schedulesError.message}
        </div>
      );
    }

    if (!schedules || schedules.length === 0) {
      return (
        <div className="rounded border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300">
          No schedules yet. Create one using the form.
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {schedules.map((schedule: HuntSchedule) => {
          const status = runStatus[schedule.id] ?? { status: 'idle' };
          return (
            <article
              key={schedule.id}
              className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 shadow-md shadow-slate-950/30"
            >
              <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-slate-100">{schedule.name}</h3>
                    {!schedule.enabled && <span className="rounded bg-slate-700 px-2 py-1 text-xs">Disabled</span>}
                  </div>
                  {schedule.description && <p className="text-sm text-slate-300">{schedule.description}</p>}
                  <dl className="grid gap-1 text-xs text-slate-400 md:grid-cols-2">
                    <div>
                      <dt className="font-semibold text-slate-300">Playbook</dt>
                      <dd>{schedule.playbook_id}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-slate-300">Cron</dt>
                      <dd>{schedule.cron_expression}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-slate-300">Last run</dt>
                      <dd>{schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString() : '—'}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-slate-300">Next run</dt>
                      <dd>{schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : '—'}</dd>
                    </div>
                  </dl>
                </div>
                <div className="flex flex-col gap-2 text-sm">
                  <button
                    type="button"
                    onClick={() => handleEdit(schedule)}
                    className="rounded border border-slate-700 px-3 py-1 text-slate-200 hover:border-slate-500"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRun(schedule.id)}
                    disabled={status.status === 'loading'}
                    className="rounded bg-sky-600 px-3 py-1 text-white hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-slate-700"
                  >
                    {status.status === 'loading' ? 'Scheduling…' : 'Run now'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(schedule.id)}
                    className="rounded bg-rose-600 px-3 py-1 text-white hover:bg-rose-500"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {status.status === 'error' && (
                <div className="mt-3 rounded border border-rose-500/40 bg-rose-900/30 p-2 text-xs text-rose-100">
                  Failed to trigger run: {status.error}
                </div>
              )}
              {status.status === 'success' && (
                <div className="mt-3 rounded border border-sky-500/40 bg-sky-900/30 p-2 text-xs text-sky-200">
                  Run dispatched to the worker.
                </div>
              )}
            </article>
          );
        })}
      </div>
    );
  }, [handleDelete, handleEdit, handleRun, runStatus, schedules, schedulesError, schedulesLoading]);

  const formPlaybookOptions = useMemo(() => {
    if (playbooksLoading) {
      return <option value="">Loading playbooks…</option>;
    }
    if (playbooksError) {
      return <option value="">Failed to load playbooks</option>;
    }
    if (!playbooks || playbooks.length === 0) {
      return <option value="">No playbooks available</option>;
    }

    return (
      <>
        <option value="">Select playbook…</option>
        {playbooks.map((playbook: Playbook) => (
          <option key={playbook.id} value={playbook.id}>
            {playbook.name}
          </option>
        ))}
      </>
    );
  }, [playbooks, playbooksError, playbooksLoading]);

  return (
    <section className="space-y-8">
      <header className="space-y-1">
        <h2 className="text-2xl font-semibold text-slate-100">Hunt schedules</h2>
        <p className="text-sm text-slate-400">
          Create recurring hunts and trigger ad-hoc runs backed by the Celery worker.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/60 p-6 shadow shadow-slate-950/40"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="flex flex-col gap-2 text-sm text-slate-200">
            <span>Name</span>
            <input
              required
              value={formState.name}
              onChange={(event: ChangeEvent<HTMLInputElement>) => handleInputChange('name', event.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:outline-none"
              placeholder="Daily threat sweep"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-200">
            <span>Playbook</span>
            <select
              required
              value={formState.playbook_id}
              onChange={(event: ChangeEvent<HTMLSelectElement>) => handleInputChange('playbook_id', event.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:outline-none"
            >
              {formPlaybookOptions}
            </select>
          </label>
          <label className="md:col-span-2 flex flex-col gap-2 text-sm text-slate-200">
            <span>Description</span>
            <textarea
              value={formState.description}
              onChange={(event: ChangeEvent<HTMLTextAreaElement>) => handleInputChange('description', event.target.value)}
              className="h-24 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:outline-none"
              placeholder="Context for analysts or linked detection"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-200">
            <span>Cron expression</span>
            <input
              required
              value={formState.cron_expression}
              onChange={(event: ChangeEvent<HTMLInputElement>) => handleInputChange('cron_expression', event.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:outline-none"
              placeholder="0 * * * *"
            />
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-200">
            <input
              type="checkbox"
              checked={formState.enabled}
              onChange={(event: ChangeEvent<HTMLInputElement>) => handleInputChange('enabled', event.target.checked)}
              className="h-4 w-4 rounded border border-slate-600 bg-slate-950 text-sky-500 focus:ring-sky-500"
            />
            Enabled
          </label>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="rounded bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700"
            disabled={createMutation.isLoading || updateMutation.isLoading}
          >
            {editingId ? 'Update schedule' : 'Create schedule'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={handleCancelEdit}
              className="rounded border border-slate-600 px-4 py-2 text-sm text-slate-200 hover:border-slate-400"
            >
              Cancel
            </button>
          )}
        </div>

        {(createMutation.isError || updateMutation.isError) && (
          <div className="rounded border border-rose-500/40 bg-rose-900/30 p-3 text-xs text-rose-100">
            {createMutation.error instanceof Error
              ? createMutation.error.message
              : updateMutation.error instanceof Error
              ? updateMutation.error.message
              : 'Unable to save schedule.'}
          </div>
        )}

        {createMutation.isSuccess && !editingId && (
          <div className="rounded border border-sky-500/40 bg-sky-900/30 p-3 text-xs text-sky-100">
            Schedule created successfully.
          </div>
        )}

        {updateMutation.isSuccess && editingId === null && (
          <div className="rounded border border-sky-500/40 bg-sky-900/30 p-3 text-xs text-sky-100">
            Schedule updated successfully.
          </div>
        )}
      </form>

      {scheduleCards}
    </section>
  );
}
