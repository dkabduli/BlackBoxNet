import { Box } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useScenario } from '../../context/ScenarioContext';
import { VENDOR_GROUP_META, VENDOR_GROUP_ORDER, type VendorGroupId } from '../../lib/vendorGroups';
import { cn } from '../../lib/utils';

export default function VendorNav() {
  const { activeVendorGroup, selectVendorGroup, ready, scenarioSwitching } = useScenario();

  return (
    <div className="flex items-center gap-3 min-w-0">
      <Link to="/" className="flex shrink-0 items-center gap-2">
        <Box className="h-6 w-6 text-blue-400" />
        <span className="text-lg font-bold text-white">BlackBoxNet</span>
      </Link>

      <div className="hidden h-8 w-px bg-gray-700 sm:block" aria-hidden />

      <div
        className="flex items-center gap-1 overflow-x-auto"
        role="tablist"
        aria-label="Vendor platform"
      >
        {VENDOR_GROUP_ORDER.map((group) => {
          const meta = VENDOR_GROUP_META[group];
          const active = activeVendorGroup === group;
          return (
            <button
              key={group}
              type="button"
              role="tab"
              aria-selected={active}
              disabled={!ready || scenarioSwitching}
              onClick={() => selectVendorGroup(group as VendorGroupId)}
              className={cn(
                'flex flex-col items-start rounded-lg px-3 py-1.5 text-left transition-colors whitespace-nowrap',
                active ? meta.activeClass : meta.idleClass,
                (!ready || scenarioSwitching) && 'opacity-50 cursor-wait'
              )}
            >
              <span className="text-sm font-semibold leading-tight">{meta.label}</span>
              <span className="text-[10px] opacity-80">{meta.subtitle}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
