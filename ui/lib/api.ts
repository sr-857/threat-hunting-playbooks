/// <reference types="node" />

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return (await response.json()) as T;
}

export interface Playbook {
  id: string;
  name: string;
  description?: string | null;
  rule_path: string;
  data_path: string;
  data_format: string;
  tags: string[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface PlaybookRunMatch {
  record: Record<string, unknown>;
  matched: boolean;
  reason?: string | null;
}

export interface PlaybookRunResult {
  playbook_id: string;
  matches: PlaybookRunMatch[];
  total_records: number;
  matched_count: number;
  execution_notes?: string | null;
}

export interface PlaybookRunResponse {
  playbook: Playbook;
  result: PlaybookRunResult;
}

export interface HuntSchedule {
  id: string;
  name: string;
  description?: string | null;
  playbook_id: string;
  cron_expression: string;
  enabled: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateScheduleInput {
  name: string;
  description?: string | null;
  playbook_id: string;
  cron_expression: string;
  enabled?: boolean;
}

export interface UpdateScheduleInput {
  name?: string;
  description?: string | null;
  cron_expression?: string;
  enabled?: boolean;
}

export interface TelemetryEvent {
  type: string;
  timestamp: string;
  playbook_id: string;
  trigger?: string;
  schedule_id?: string | null;
  matched_count?: number;
  total_records?: number;
  confidence?: number;
  notes?: string | null;
  error?: string;
}

export interface TelemetryAlert {
  type: string;
  timestamp: string;
  playbook_id: string;
  trigger?: string;
  schedule_id?: string | null;
  confidence: number;
  threshold: number;
}

export async function fetchPlaybooks(): Promise<Playbook[]> {
  const response = await fetch(`${API_BASE_URL}/api/playbooks/`, {
    cache: 'no-store',
  });
  return handleResponse<Playbook[]>(response);
}

export async function fetchPlaybook(playbookId: string): Promise<Playbook> {
  const response = await fetch(`${API_BASE_URL}/api/playbooks/${playbookId}`, {
    cache: 'no-store',
  });
  return handleResponse<Playbook>(response);
}

export async function runPlaybook(playbookId: string): Promise<PlaybookRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/playbooks/${playbookId}/run`, {
    method: 'POST',
  });
  return handleResponse<PlaybookRunResponse>(response);
}

export async function fetchSchedules(): Promise<HuntSchedule[]> {
  const response = await fetch(`${API_BASE_URL}/api/schedules/`, {
    cache: 'no-store',
  });
  return handleResponse<HuntSchedule[]>(response);
}

export async function createSchedule(input: CreateScheduleInput): Promise<HuntSchedule> {
  const response = await fetch(`${API_BASE_URL}/api/schedules/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...input,
      description: input.description ?? null,
      enabled: input.enabled ?? true,
    }),
  });
  return handleResponse<HuntSchedule>(response);
}

export async function updateSchedule(
  scheduleId: string,
  data: UpdateScheduleInput,
): Promise<HuntSchedule> {
  const response = await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<HuntSchedule>(response);
}

export async function deleteSchedule(scheduleId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
}

export async function runSchedule(scheduleId: string): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}/run`, {
    method: 'POST',
  });
  return handleResponse<{ status: string }>(response);
}

export async function fetchTelemetryEvents(limit = 50): Promise<TelemetryEvent[]> {
  const response = await fetch(`${API_BASE_URL}/api/telemetry/events?limit=${limit}`, {
    cache: 'no-store',
  });
  return handleResponse<TelemetryEvent[]>(response);
}

export async function fetchTelemetryAlerts(limit = 50): Promise<TelemetryAlert[]> {
  const response = await fetch(`${API_BASE_URL}/api/telemetry/alerts?limit=${limit}`, {
    cache: 'no-store',
  });
  return handleResponse<TelemetryAlert[]>(response);
}
