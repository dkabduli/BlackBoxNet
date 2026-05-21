import { Clock } from 'lucide-react';

export default function DemoColdStartBanner() {
  if (import.meta.env.VITE_SHOW_DEMO_BANNER !== 'true') {
    return null;
  }

  return (
    <div className="border-b border-amber-500/30 bg-amber-500/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex items-start gap-2 text-sm text-amber-200/90">
        <Clock className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
        <p>
          <span className="font-medium text-amber-100">Public demo on Render free tier.</span>{' '}
          The API sleeps after ~15 min idle — the first simulation click after that may take
          30–60 seconds to wake up. Refresh or wait once, then run T1→T5.
        </p>
      </div>
    </div>
  );
}
