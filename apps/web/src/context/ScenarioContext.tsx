import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { getScenarios, getSimulationStatus, resetSimulation, apiErrorMessage } from '../api/client';
import type { ScenarioCatalogItem } from '../types';
import type { VendorGroupId } from '../lib/vendorGroups';
import { VENDOR_GROUP_ORDER } from '../lib/vendorGroups';

interface ScenarioContextValue {
  scenarios: ScenarioCatalogItem[];
  scenariosForVendor: ScenarioCatalogItem[];
  activeVendorGroup: VendorGroupId;
  selectVendorGroup: (group: VendorGroupId) => void;
  activeScenarioId: string;
  selectScenario: (scenarioId: string) => void;
  activeScenario: ScenarioCatalogItem | undefined;
  ready: boolean;
  scenarioSwitching: boolean;
  refreshNonce: number;
  bootstrapError: string | null;
  refreshCatalog: () => Promise<void>;
}

const ScenarioContext = createContext<ScenarioContextValue | null>(null);

const RESET_CONFIRM_MSG =
  'Switching scenario resets the selected scenario to T1 and clears its devices and incidents. Continue?';

function groupOf(sc: ScenarioCatalogItem): VendorGroupId {
  const g = sc.vendor_group as VendorGroupId | undefined;
  if (g && VENDOR_GROUP_ORDER.includes(g)) return g;
  return 'cisco';
}

function firstScenarioInGroup(
  list: ScenarioCatalogItem[],
  group: VendorGroupId
): ScenarioCatalogItem | undefined {
  return list
    .filter((s) => groupOf(s) === group)
    .sort((a, b) => a.tab_order - b.tab_order)[0];
}

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const [scenarios, setScenarios] = useState<ScenarioCatalogItem[]>([]);
  const [activeVendorGroup, setActiveVendorGroupState] = useState<VendorGroupId>('cisco');
  const [activeScenarioId, setActiveScenarioId] = useState('acl-regression');
  const [ready, setReady] = useState(false);
  const [scenarioSwitching, setScenarioSwitching] = useState(false);
  const [refreshNonce, setRefreshNonce] = useState(0);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);
  const scenariosRef = useRef<ScenarioCatalogItem[]>([]);
  const activeScenarioIdRef = useRef(activeScenarioId);
  const activeVendorGroupRef = useRef(activeVendorGroup);
  scenariosRef.current = scenarios;
  activeScenarioIdRef.current = activeScenarioId;
  activeVendorGroupRef.current = activeVendorGroup;

  const scenariosForVendor = useMemo(
    () =>
      scenarios
        .filter((s) => groupOf(s) === activeVendorGroup)
        .sort((a, b) => a.tab_order - b.tab_order),
    [scenarios, activeVendorGroup]
  );

  const confirmSwitchIfNeeded = useCallback(async (targetScenarioId: string): Promise<boolean> => {
    const currentId = activeScenarioIdRef.current;
    if (targetScenarioId === currentId) return false;
    try {
      const status = await getSimulationStatus(currentId);
      const hasProgress = (status?.progress?.percentage ?? 0) > 0;
      if (hasProgress && typeof window !== 'undefined') {
        return window.confirm(RESET_CONFIRM_MSG);
      }
    } catch {
      return true;
    }
    return true;
  }, []);

  const resetAndActivate = useCallback(
    async (
      scenarioId: string,
      vendorGroup?: VendorGroupId,
      options?: { skipConfirm?: boolean }
    ) => {
      if (!options?.skipConfirm) {
        const ok = await confirmSwitchIfNeeded(scenarioId);
        if (!ok) return;
      }

      setScenarioSwitching(true);
      setBootstrapError(null);
      try {
        await resetSimulation(scenarioId);
        if (vendorGroup) setActiveVendorGroupState(vendorGroup);
        setActiveScenarioId(scenarioId);
        setRefreshNonce((n) => n + 1);
      } catch (e) {
        console.error('Scenario reset failed', e);
        setBootstrapError(apiErrorMessage(e, 'Failed to reset scenario to T1'));
      } finally {
        setScenarioSwitching(false);
      }
    },
    [confirmSwitchIfNeeded]
  );

  const selectScenario = useCallback(
    (scenarioId: string) => {
      if (scenarioId === activeScenarioIdRef.current) return;
      const sc = scenariosRef.current.find((s) => s.id === scenarioId);
      if (!sc) {
        setBootstrapError(`Unknown scenario: ${scenarioId}`);
        return;
      }
      setActiveVendorGroupState(groupOf(sc));
      void resetAndActivate(scenarioId);
    },
    [resetAndActivate]
  );

  const selectVendorGroup = useCallback(
    (group: VendorGroupId) => {
      if (group === activeVendorGroupRef.current) return;
      const first = firstScenarioInGroup(scenariosRef.current, group);
      if (!first) return;
      void resetAndActivate(first.id, group);
    },
    [resetAndActivate]
  );

  const refreshCatalog = useCallback(async () => {
    const list = await getScenarios();
    setScenarios(list);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setBootstrapError(null);
        const list = await getScenarios();
        if (cancelled) return;
        setScenarios(list);
        if (list.length === 0) {
          setBootstrapError('No scenarios loaded from API. Check server logs and mock-scenarios package.');
        } else {
          const preferred =
            list.find((s: ScenarioCatalogItem) => s.id === 'acl-regression') ??
            firstScenarioInGroup(list, 'cisco') ??
            list[0];
          setActiveVendorGroupState(groupOf(preferred));
          setActiveScenarioId(preferred.id);
          const onRender =
            typeof window !== 'undefined' &&
            window.location.hostname.endsWith('.onrender.com');
          if (!onRender) {
            setScenarioSwitching(true);
            await resetSimulation(preferred.id);
            if (cancelled) return;
            setRefreshNonce((n) => n + 1);
          }
        }
      } catch (e) {
        if (!cancelled) {
          setBootstrapError(apiErrorMessage(e, 'Failed to load scenarios'));
        }
      } finally {
        if (!cancelled) {
          setScenarioSwitching(false);
          setReady(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeScenario = useMemo(
    () => scenarios.find((s) => s.id === activeScenarioId),
    [scenarios, activeScenarioId]
  );

  const value = useMemo(
    () => ({
      scenarios,
      scenariosForVendor,
      activeVendorGroup,
      selectVendorGroup,
      activeScenarioId,
      selectScenario,
      activeScenario,
      ready,
      scenarioSwitching,
      refreshNonce,
      bootstrapError,
      refreshCatalog,
    }),
    [
      scenarios,
      scenariosForVendor,
      activeVendorGroup,
      selectVendorGroup,
      activeScenarioId,
      selectScenario,
      activeScenario,
      ready,
      scenarioSwitching,
      refreshNonce,
      bootstrapError,
      refreshCatalog,
    ]
  );

  return <ScenarioContext.Provider value={value}>{children}</ScenarioContext.Provider>;
}

export function useScenario() {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error('useScenario must be used within ScenarioProvider');
  return ctx;
}
