import { Suspense } from 'react';

import { PlaybookList } from '@/components/playbooks/playbook-list';

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 p-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Threat Hunting Playbooks</h1>
        <p className="text-slate-300">Browse, run, and review hunts backed by Sigma/YARA detections.</p>
      </header>
      <Suspense fallback={<div className="text-slate-400">Loading playbooks...</div>}>
        <PlaybookList />
      </Suspense>
    </main>
  );
}
