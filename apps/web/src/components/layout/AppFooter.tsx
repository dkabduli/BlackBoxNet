import { Box } from 'lucide-react';

export default function AppFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-12 border-t border-gray-800 bg-gray-900/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <Box className="h-5 w-5 shrink-0 text-blue-400 mt-0.5" aria-hidden />
            <div>
              <p className="text-sm font-medium text-gray-200">
                BlackBoxNet — outage correlation &amp; config diff demo
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Cisco, Juniper, and Nokia scenarios · T1→T5 simulation · topology + semantic diffs
              </p>
            </div>
          </div>
          <div className="text-left sm:text-right">
            <p className="text-sm text-gray-300">
              Built by <span className="font-semibold text-white">Abdul Rehman</span>
            </p>
            <p className="text-xs text-gray-500 mt-1">
              © {year} · Phase 2 lab project
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
