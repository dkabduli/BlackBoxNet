import { useState, useEffect, useCallback } from 'react';
import { Play, RotateCcw, Loader2, AlertCircle } from 'lucide-react';
import {
  getSimulationStatus,
  runSimulationStep,
  resetSimulation,
  apiErrorMessage,
} from '../../api/client';
import type { SimulationStatus } from '../../types';
import { useScenario } from '../../context/ScenarioContext';
import { cn } from '../../lib/utils';

interface Props {
  onStepComplete?: () => void;
}

export default function SimulationControls({ onStepComplete }: Props) {
  const { activeScenarioId, activeScenario, ready, scenarioSwitching, refreshNonce } =
    useScenario();
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!ready) return;
    setError(null);
    try {
      const data = await getSimulationStatus(activeScenarioId);
      setStatus(data);
    } catch (e) {
      console.error('Failed to fetch simulation status', e);
      setStatus(null);
      setError('Could not load simulation status. Is the API running?');
    }
  }, [activeScenarioId, ready]);

  useEffect(() => {
    setStatus(null);
    if (ready && !scenarioSwitching) fetchStatus();
  }, [fetchStatus, ready, activeScenarioId, refreshNonce, scenarioSwitching]);

  const handleStep = async () => {
    setLoading(true);
    setError(null);
    try {
      await runSimulationStep(activeScenarioId);
      await fetchStatus();
      onStepComplete?.();
    } catch (e) {
      console.error('Step failed', e);
      setError(apiErrorMessage(e, 'Run step failed. Check API logs.'));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    setError(null);
    try {
      await resetSimulation(activeScenarioId);
      await fetchStatus();
      onStepComplete?.();
    } catch (e) {
      console.error('Reset failed', e);
      setError(apiErrorMessage(e, 'Reset failed'));
    } finally {
      setResetting(false);
    }
  };

  if (!ready || scenarioSwitching) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 text-sm text-gray-500">
        {scenarioSwitching ? 'Resetting to T1…' : 'Loading scenarios…'}
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-5">
        <div className="flex items-start gap-2 text-sm text-red-200">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
        <button
          onClick={fetchStatus}
          className="mt-3 text-xs text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 text-sm text-gray-500">
        Loading simulation…
      </div>
    );
  }

  const pct = status.progress.percentage;
  const stepSequence = ['T1', 'T2', 'T3', 'T4', 'T5'];
  const stepLabels = status.step_labels ?? {};
  const currentDescription =
    status.current_step_description ||
    stepLabels[status.current_step] ||
    'Simulation checkpoint';
  const canRun = status.progress.can_run_current_step;
  const runLabel = status.progress.is_complete
    ? 'Complete'
    : `Run ${status.progress.next_step || status.current_step}`;
  const demoPath = status.demo_path || activeScenario?.demo_path || '';

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-white text-sm">Simulation</h3>
          <p className="text-xs text-gray-400 mt-0.5">{demoPath}</p>
          <p className="text-[11px] text-gray-500 mt-1">
            {status.current_step}: {currentDescription}
          </p>
        </div>
        <span className="text-lg font-mono font-bold text-blue-400">{status.current_step}</span>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span>{pct}%</span>
        </div>
        <div
          className="h-2 bg-gray-800 rounded-full overflow-hidden"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Simulation progress"
        >
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
              title={stepLabels[step]}
            >
              {step}
            </span>
          ))}
        </div>
      </div>

      {error && (
        <p className="mb-2 text-xs text-amber-400">{error}</p>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleStep}
          disabled={loading || !canRun}
          aria-label={loading ? 'Running simulation step' : runLabel}
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
          aria-label={resetting ? 'Resetting simulation' : 'Reset simulation to T1'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
        >
          {resetting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          Reset
        </button>
      </div>
    </div>
  );
}
