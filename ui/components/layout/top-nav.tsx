"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_LINKS = [
  { href: '/', label: 'Playbooks' },
  { href: '/guides', label: 'Guided Workflow' },
  { href: '/advanced', label: 'Advanced Mode' },
];

export function TopNav() {
  const pathname = usePathname();

  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900/60 px-6 py-4 backdrop-blur">
      <Link href="/" className="text-lg font-semibold text-sky-400">
        Threat Hunting Playbooks
      </Link>
      <nav className="flex items-center gap-6 text-sm uppercase tracking-wide text-slate-300">
        {NAV_LINKS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${isActive ? 'text-sky-300' : 'hover:text-sky-200'} transition-colors`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="text-xs text-slate-400">v0.1 • Local Mode</div>
    </header>
  );
}
