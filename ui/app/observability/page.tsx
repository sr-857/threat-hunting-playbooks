import { ObservabilityDashboard } from '@/components/observability/observability-dashboard';

export default function ObservabilityPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 p-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-slate-100">Observability</h1>
        <p className="text-slate-300">
          Monitor hunt executions, confidence trends, and alerts in near real time.
        </p>
      </header>
      <ObservabilityDashboard defaultLimit={50} />
    </main>
  );
}
