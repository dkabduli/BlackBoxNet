import { Outlet, Link, useLocation } from 'react-router-dom';
import { Activity, Server, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';
import DemoColdStartBanner from './DemoColdStartBanner';
import VendorNav from './VendorNav';

const navItems = [
  { path: '/', label: 'Dashboard', icon: Activity },
  { path: '/devices', label: 'Devices', icon: Server },
  { path: '/incidents', label: 'Incidents', icon: AlertTriangle },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <VendorNav />
            <nav className="flex shrink-0 items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-blue-500/20 text-blue-400'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </header>
      <DemoColdStartBanner />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
