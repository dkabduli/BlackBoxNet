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
import { getScenarios, resetSimulation, apiErrorMessage } from '../api/client';
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
  scenariosRef.current = scenarios;

  const scenariosForVendor = useMemo(
    () =>
      scenarios
        .filter((s) => groupOf(s) === activeVendorGroup)
        .sort((a, b) => a.tab_order - b.tab_order),
    [scenarios, activeVendorGroup]
  );

  const resetAndActivate = useCallback(async (scenarioId: string, vendorGroup?: VendorGroupId) => {
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
  }, []);

  const selectScenario = useCallback(
    (scenarioId: string) => {
      const sc = scenariosRef.current.find((s) => s.id === scenarioId);
      if (sc) setActiveVendorGroupState(groupOf(sc));
      void resetAndActivate(scenarioId);
    },
    [resetAndActivate]
  );

  const selectVendorGroup = useCallback(
    (group: VendorGroupId) => {
      const first = firstScenarioInGroup(scenariosRef.current, group);
      if (!first) return;
      void resetAndActivate(first.id, group);
    },
    [resetAndActivate]
  );

  const refreshCatalog = useCallback(async () => {
    const list = await getScenarios();
    setScenarios(list);
    return list;
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setBootstrapError(null);
        const list = await getScenarios();
        if (cancelled) return;
        setScenarios(list);
        if (list.length) {
          const preferred =
            list.find((s: ScenarioCatalogItem) => s.id === 'acl-regression') ??
            firstScenarioInGroup(list, 'cisco') ??
            list[0];
          setActiveVendorGroupState(groupOf(preferred));
          setActiveScenarioId(preferred.id);
          // Skip auto-reset on Render (POST preflight + cold start); user clicks Reset once.
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

  return (
    <ScenarioContext.Provider value={value}>{children}</ScenarioContext.Provider>
  );
}

export function useScenario() {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error('useScenario must be used within ScenarioProvider');
  return ctx;
}
