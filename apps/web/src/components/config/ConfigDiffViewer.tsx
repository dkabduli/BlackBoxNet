import { useState, useEffect } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { getConfigDiff } from '../../api/client';
import type { ConfigDiff } from '../../types';
import { suspicionColor, cn } from '../../lib/utils';

interface Props {
  deviceId: string;
  diffId: string;
  onClose: () => void;
}

function DiffLine({ line, idx }: { line: string; idx: number }) {
  let bg = '';
  let textColor = 'text-gray-300';

  if (line.startsWith('+') && !line.startsWith('+++')) {
    bg = 'bg-green-500/10';
    textColor = 'text-green-400';
  } else if (line.startsWith('-') && !line.startsWith('---')) {
    bg = 'bg-red-500/10';
    textColor = 'text-red-400';
  } else if (line.startsWith('@@')) {
    bg = 'bg-blue-500/10';
    textColor = 'text-blue-400';
  }

  return (
    <div className={cn('flex text-xs font-mono', bg)}>
      <span className="w-8 text-right pr-2 text-gray-600 select-none flex-shrink-0">{idx + 1}</span>
      <pre className={cn('flex-1 px-2 py-0.5 whitespace-pre-wrap', textColor)}>{line}</pre>
    </div>
  );
}

export default function ConfigDiffViewer({ deviceId, diffId, onClose }: Props) {
  const [diff, setDiff] = useState<ConfigDiff | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getConfigDiff(deviceId, diffId)
      .then(setDiff)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [deviceId, diffId]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-gray-900 rounded-xl p-8 text-gray-400">Loading diff...</div>
      </div>
    );
  }

  if (!diff) return null;

  const lines = diff.diff_text.split('\n');

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl border border-gray-700 w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div>
            <h3 className="font-semibold text-white">Config Diff — {diff.device_hostname}</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              +{diff.lines_added} / -{diff.lines_removed} lines
            </p>
            {(diff.config_source === 'ssh' || diff.redacted) && (
              <div className="mt-2 flex gap-2 text-[11px]">
                {diff.config_source === 'ssh' && (
                  <span className="rounded bg-blue-500/20 px-2 py-1 text-blue-300">live ssh source</span>
                )}
                {diff.redacted && (
                  <span className="rounded bg-amber-500/20 px-2 py-1 text-amber-300">secrets redacted</span>
                )}
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className={cn('px-2 py-1 rounded text-xs font-medium', suspicionColor(diff.suspicion_level))}>
              {diff.suspicion_level.toUpperCase()} SUSPICION
            </span>
            <button onClick={onClose} className="p-1 rounded hover:bg-gray-800 text-gray-400">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {diff.semantic_summary.length > 0 && (
          <div className="p-4 border-b border-gray-800 space-y-2">
            <h4 className="text-xs font-semibold text-gray-400 uppercase">Semantic Analysis</h4>
            {diff.semantic_summary.map((s, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <AlertTriangle className={cn('w-3.5 h-3.5 mt-0.5 flex-shrink-0',
                  s.suspicion_level === 'high' ? 'text-orange-400' : 'text-yellow-400'
                )} />
                <div>
                  <span className="font-medium text-white">{s.entity}</span>
                  <span className="text-gray-400"> — {s.reason}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-auto p-2 bg-gray-950 rounded-b-xl">
          {lines.map((line, i) => (
            <DiffLine key={i} line={line} idx={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
