import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityColor(severity: string): string {
  switch (severity) {
    case 'CRITICAL': return 'text-red-400 bg-red-400/10 border-red-400/30';
    case 'ERROR': return 'text-orange-400 bg-orange-400/10 border-orange-400/30';
    case 'WARNING': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
    case 'INFO': return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
    default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
  }
}

export function healthColor(status: string): string {
  switch (status) {
    case 'healthy': return 'text-green-400';
    case 'degraded': return 'text-yellow-400';
    case 'critical': return 'text-red-400';
    default: return 'text-gray-400';
  }
}

export function healthBg(status: string): string {
  switch (status) {
    case 'healthy': return 'bg-green-400/10 border-green-400/30';
    case 'degraded': return 'bg-yellow-400/10 border-yellow-400/30';
    case 'critical': return 'bg-red-400/10 border-red-400/30';
    default: return 'bg-gray-400/10 border-gray-400/30';
  }
}

export function suspicionColor(level: string): string {
  switch (level) {
    case 'critical': return 'text-red-400 bg-red-500/20';
    case 'high': return 'text-orange-400 bg-orange-500/20';
    case 'medium': return 'text-yellow-400 bg-yellow-500/20';
    case 'low': return 'text-green-400 bg-green-500/20';
    default: return 'text-gray-400 bg-gray-500/20';
  }
}

export function formatTimestamp(ts: string): string {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false });
}
