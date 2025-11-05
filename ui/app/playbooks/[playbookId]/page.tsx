import { notFound } from 'next/navigation';

import { PlaybookDetail } from '@/components/playbooks/playbook-detail';
import { fetchPlaybook } from '@/lib/api';

type PageProps = {
  params: {
    playbookId: string;
  };
};

export default async function PlaybookDetailPage({ params }: PageProps) {
  const { playbookId } = params;

  try {
    await fetchPlaybook(playbookId);
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      notFound();
    }
  }

  return <PlaybookDetail playbookId={playbookId} />;
}
