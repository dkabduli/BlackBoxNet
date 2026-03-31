import { useState, useEffect } from 'react';
import { Play, RotateCcw, Loader2 } from 'lucide-react';
import { getSimulationStatus, runSimulationStep, resetSimulation } from '../../api/client';
import type { SimulationStatus } from '../../types';
import { cn } from '../../lib/utils';

interface Props {
  onStepComplete?: () => void;
}

const stepDescriptions: Record<string, string> = {
  T1: 'Baseline healthy',
  T2: 'ACL change introduced',
  T3: 'Degradation detected',
  T4: 'Resource stress',
  T5: 'Outage peak',
};

const demoPath = 'PC subnet 10.0.1.0/24 -> access-switch-1 -> dist-switch-1 -> edge-router-1';

export default function SimulationControls({ onStepComplete }: Props) {
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await getSimulationStatus();
      setStatus(data);
    } catch (e) {
      console.error('Failed to fetch simulation status', e);
    }
  };

  useEffect(() => { fetchStatus(); }, []);

  const handleStep = async () => {
    setLoading(true);
    try {
      await runSimulationStep();
      await fetchStatus();
      onStepComplete?.();
    } catch (e) {
      console.error('Step failed', e);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    try {
      await resetSimulation();
      await fetchStatus();
      onStepComplete?.();
    } catch (e) {
      console.error('Reset failed', e);
    } finally {
      setResetting(false);
    }
  };

  if (!status) return null;

  const pct = status.progress.percentage;
  const stepSequence = ['T1', 'T2', 'T3', 'T4', 'T5'];
  const currentDescription = stepDescriptions[status.current_step] ?? 'Simulation checkpoint';
  const canRun = status.progress.can_run_current_step;
  const runLabel = status.progress.is_complete
    ? 'Complete'
    : `Run ${status.progress.next_step || status.current_step}`;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-white text-sm">Simulation</h3>
          <p className="text-xs text-gray-400 mt-0.5">{demoPath}</p>
          <p className="text-[11px] text-gray-500 mt-1">{status.current_step}: {currentDescription}</p>
        </div>
        <span className="text-lg font-mono font-bold text-blue-400">{status.current_step}</span>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span>{pct}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-2 flex justify-between text-xs text-gray-500">
          {stepSequence.map((step) => (
            <span
              key={step}
              className={cn('font-medium', step === status.current_step ? 'text-blue-400' : 'text-gray-500')}
            >
              {step}
            </span>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleStep}
          disabled={loading || !canRun}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            canRun
              ? 'bg-blue-600 hover:bg-blue-500 text-white'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
          )}
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {runLabel}
        </button>
        <button
          onClick={handleReset}
          disabled={resetting}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
        >
          {resetting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          Reset
        </button>
      </div>
    </div>
  );
}
