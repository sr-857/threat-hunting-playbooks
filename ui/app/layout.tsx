import './globals.css';
import type { Metadata } from 'next';

import { Providers } from './providers';
import { TopNav } from '@/components/layout/top-nav';

export const metadata: Metadata = {
  title: 'Threat Hunting Playbooks',
  description: 'Sigma/YARA driven hunts with enrichment workflows',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <Providers>
          <TopNav />
          <div className="mx-auto max-w-6xl px-6 pb-12">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
