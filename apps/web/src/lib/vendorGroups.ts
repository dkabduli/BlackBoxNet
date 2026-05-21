export type VendorGroupId = 'cisco' | 'juniper' | 'nokia';

export const VENDOR_GROUP_ORDER: VendorGroupId[] = ['cisco', 'juniper', 'nokia'];

export const VENDOR_GROUP_META: Record<
  VendorGroupId,
  { label: string; subtitle: string; activeClass: string; idleClass: string }
> = {
  cisco: {
    label: 'Cisco',
    subtitle: 'IOS',
    activeClass: 'bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/40',
    idleClass: 'text-gray-400 hover:text-emerald-300 hover:bg-emerald-500/10',
  },
  juniper: {
    label: 'Juniper',
    subtitle: 'Junos',
    activeClass: 'bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/40',
    idleClass: 'text-gray-400 hover:text-amber-300 hover:bg-amber-500/10',
  },
  nokia: {
    label: 'Nokia',
    subtitle: 'SR OS',
    activeClass: 'bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/40',
    idleClass: 'text-gray-400 hover:text-violet-300 hover:bg-violet-500/10',
  },
};
