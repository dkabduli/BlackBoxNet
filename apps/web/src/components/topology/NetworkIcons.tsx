export const RouterIcon = ({ size = 48, color = '#4ade80' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <circle cx="32" cy="32" r="22" stroke={color} strokeWidth="2.5" fill="none" />
    <circle cx="32" cy="32" r="8" fill={color} fillOpacity="0.2" stroke={color} strokeWidth="1.5" />
    <path d="M32 14v6M32 44v6M14 32h6M44 32h6" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <path d="M32 20l-3 4h6l-3-4z" fill={color} />
    <path d="M32 44l3-4h-6l3 4z" fill={color} />
    <path d="M20 32l4-3v6l-4-3z" fill={color} />
    <path d="M44 32l-4 3v-6l4 3z" fill={color} />
  </svg>
);

export const SwitchIcon = ({ size = 48, color = '#4ade80' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <rect x="8" y="22" width="48" height="20" rx="4" stroke={color} strokeWidth="2" fill={color} fillOpacity="0.1" />
    <rect x="14" y="27" width="5" height="10" rx="1" fill={color} fillOpacity="0.5" />
    <rect x="22" y="27" width="5" height="10" rx="1" fill={color} fillOpacity="0.5" />
    <rect x="30" y="27" width="5" height="10" rx="1" fill={color} fillOpacity="0.5" />
    <rect x="38" y="27" width="5" height="10" rx="1" fill={color} fillOpacity="0.5" />
    <path d="M20 18l-6 4h12l-6-4z" fill={color} />
    <path d="M44 18l-6 4h12l-6-4z" fill={color} />
    <path d="M14 22h12M38 22h12" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const FirewallIcon = ({ size = 48, color = '#4ade80' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <path
      d="M32 8 L52 18 L52 34 Q52 50 32 58 Q12 50 12 34 L12 18 Z"
      stroke={color}
      strokeWidth="2.5"
      fill={color}
      fillOpacity="0.1"
    />
    <path
      d="M22 32l7 7 13-13"
      stroke={color}
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const UsersIcon = ({ size = 48, color = '#f87171' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <circle cx="22" cy="22" r="8" stroke={color} strokeWidth="2" fill="none" />
    <path
      d="M8 48 Q8 36 22 36 Q36 36 36 48"
      stroke={color}
      strokeWidth="2"
      fill="none"
      strokeLinecap="round"
    />
    <circle cx="42" cy="20" r="6" stroke={color} strokeWidth="1.5" fill="none" />
    <path
      d="M32 44 Q32 34 42 34 Q52 34 52 44"
      stroke={color}
      strokeWidth="1.5"
      fill="none"
      strokeLinecap="round"
    />
  </svg>
);

export const ServerIcon = ({ size = 48, color = '#60a5fa' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <rect x="14" y="10" width="36" height="12" rx="3" stroke={color} strokeWidth="2" fill={color} fillOpacity="0.1" />
    <rect x="14" y="26" width="36" height="12" rx="3" stroke={color} strokeWidth="2" fill={color} fillOpacity="0.1" />
    <rect x="14" y="42" width="36" height="12" rx="3" stroke={color} strokeWidth="2" fill={color} fillOpacity="0.1" />
    <circle cx="44" cy="16" r="2" fill={color} />
    <circle cx="44" cy="32" r="2" fill={color} />
    <circle cx="44" cy="48" r="2" fill={color} />
  </svg>
);

export const CloudIcon = ({ size = 48, color = '#818cf8' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <path
      d="M14 42 Q8 42 8 34 Q8 26 16 26 Q16 18 24 16 Q32 14 38 20 Q44 14 50 18 Q58 22 56 32 Q60 34 58 42Z"
      stroke={color}
      strokeWidth="2"
      fill={color}
      fillOpacity="0.1"
    />
  </svg>
);

export const FECIcon = ({ size = 48, color = '#f87171' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <rect x="12" y="18" width="40" height="9" rx="2" stroke={color} strokeWidth="1.5" fill={color} fillOpacity="0.15" />
    <rect x="12" y="29" width="40" height="9" rx="2" stroke={color} strokeWidth="1.5" fill={color} fillOpacity="0.25" />
    <rect x="12" y="40" width="40" height="9" rx="2" stroke={color} strokeWidth="1.5" fill={color} fillOpacity="0.35" />
    <text x="32" y="25" textAnchor="middle" fill={color} fontSize="6" fontWeight="600">
      FEC
    </text>
    <text x="32" y="36" textAnchor="middle" fill={color} fontSize="5">
      label
    </text>
    <text x="32" y="47" textAnchor="middle" fill={color} fontSize="5">
      131071
    </text>
  </svg>
);
