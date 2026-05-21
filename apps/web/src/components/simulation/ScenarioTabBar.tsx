import { useScenario } from '../../context/ScenarioContext';
import { cn } from '../../lib/utils';

/** Scenario tabs for the active vendor only (shown on dashboard, not in header). */
export default function ScenarioTabBar() {
  const {
    scenariosForVendor,
    activeScenarioId,
    selectScenario,
    ready,
    scenarioSwitching,
    activeVendorGroup,
  } = useScenario();

  if (!ready) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 px-4 py-3 text-sm text-gray-500">
        Loading scenarios…
      </div>
    );
  }

  if (scenariosForVendor.length === 0) {
    return null;
  }

  return (
    <div
      className="flex flex-wrap gap-2 rounded-xl border border-gray-800 bg-gray-900/50 p-2"
      role="tablist"
      aria-label={`${activeVendorGroup} scenarios`}
    >
      {scenariosForVendor.map((sc) => {
        const active = sc.id === activeScenarioId;
        return (
          <button
            key={sc.id}
            role="tab"
            aria-selected={active}
            disabled={scenarioSwitching}
            onClick={() => selectScenario(sc.id)}
            className={cn(
              'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              active
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200',
              scenarioSwitching && 'opacity-50 cursor-wait'
            )}
          >
            {sc.label}
          </button>
        );
      })}
    </div>
  );
}
