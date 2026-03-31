import { useState, useEffect } from 'react';
import { Play, RotateCcw, Loader2 } from 'lucide-react';
import { getSimulationStatus, runSimulationStep, resetSimulation } from '../../api/client';
import type { SimulationStatus } from '../../types';
import { cn } from '../../lib/utils';

interface Props {
  onStepComplete?: () => void;
}

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

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-white text-sm">Simulation</h3>
          <p className="text-xs text-gray-400 mt-0.5">{status.scenario_name}</p>
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
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>T1</span><span>T2</span><span>T3</span><span>T4</span><span>T5</span>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleStep}
          disabled={loading || !status.progress.can_advance}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            status.progress.can_advance
              ? 'bg-blue-600 hover:bg-blue-500 text-white'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
          )}
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {status.progress.can_advance ? `Run ${status.progress.next_step || 'Step'}` : 'Complete'}
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
