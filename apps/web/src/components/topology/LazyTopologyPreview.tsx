import { lazy, Suspense } from 'react';
import type { ComponentProps } from 'react';
import type TopologyPreview from './TopologyPreview';

const Topology = lazy(() => import('./TopologyPreview'));

type Props = ComponentProps<typeof TopologyPreview>;

export default function LazyTopologyPreview(props: Props) {
  return (
    <Suspense
      fallback={
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 h-[520px] flex items-center justify-center text-gray-500 text-sm">
          Loading topology…
        </div>
      }
    >
      <Topology {...props} />
    </Suspense>
  );
}
