import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLiveTelemetry } from '../hooks/useLiveTelemetry';

const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000');

const allNavItems = [
  {
    section: 'Management',
    items: [
      { 
        to: '/dashboard', 
        label: 'Manager Dash', 
        icon: 'fa-chart-pie', 
        title: 'WaterAid Manager Dashboard',
        roles: ['MANAGER', 'ADMIN', 'TECHNICIAN'] // All can see dashboard
      },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { 
        to: '/ai-alerts', 
        label: 'AI Alerts', 
        icon: 'fa-robot', 
        accent: 'text-red-300', 
        title: 'AI Predictive Alerts',
        roles: ['MANAGER', 'ADMIN'] // Techs cannot see AI alerts management
      },
      { 
        to: '/iot-telemetry', 
        label: 'IoT Telemetry', 
        icon: 'fa-satellite-dish', 
        accent: 'text-blue-300', 
        title: 'IoT Sensor Telemetry',
        roles: ['MANAGER', 'ADMIN', 'TECHNICIAN'] // All can view telemetry
      },
    ],
  },
  {
    section: 'Field Ops',
    items: [
      { 
        to: '/task-entry', 
        label: 'Task Entry', 
        icon: 'fa-clipboard-list', 
        title: 'Maintenance Task Entry',
        roles: ['MANAGER', 'ADMIN', 'TECHNICIAN'] // All can log tasks
      },
    ],
  },
  {
    section: 'System',
    items: [
      { 
        to: '/infrastructure', 
        label: 'Infrastructure', 
        icon: 'fa-network-wired', 
        title: 'Infrastructure Management',
        roles: ['MANAGER', 'ADMIN'] // Techs cannot manage infrastructure
      },
    ],
  },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // 1. Filter navigation items based on user role
  const navItems = allNavItems
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => 
        item.roles.includes(user?.role_type)
      ),
    }))
    .filter((group) => group.items.length > 0); // Remove empty sections

  // 2. Determine current page title
  const currentItem = allNavItems
    .flatMap((g) => g.items)
    .find((item) => item.to === location.pathname);
  const pageTitle = currentItem?.title || 'Dashboard';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user
    ? (
        (user.first_name?.[0] || user.username[0] || '') +
        (user.last_name?.[0] || '')
      ).toUpperCase()
    : 'U';

  const roleLabel = user?.role_type
    ? user.role_type.charAt(0) + user.role_type.slice(1).toLowerCase()
    : 'User';

  const displayName =
    user?.first_name && user?.last_name
      ? `${user.first_name.charAt(0)}. ${user.last_name}`
      : user?.username || 'User';

  // 3. WebSocket connection status (optional visual indicator)
  const { connected } = useLiveTelemetry(`${WS_BASE}/ws/telemetry/`, () => {
    // We don't need to handle messages here, just the connection status
  });

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* ============================================
          SIDEBAR
          ============================================ */}
      <aside className="w-64 bg-water-900 text-white flex flex-col shadow-xl z-20 shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-water-700">
          <i className="fa-solid fa-droplet text-xl text-blue-300 mr-3"></i>
          <span className="font-bold text-lg tracking-wide">WaterAid Ops</span>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((group, i) => (
            <div key={group.section}>
              <div
                className={`text-xs font-semibold text-water-100 uppercase tracking-wider mb-2 px-2 ${
                  i === 0 ? 'mt-4' : 'mt-6'
                }`}
              >
                {group.section}
              </div>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center px-4 py-3 rounded-lg transition ${
                      isActive ? 'bg-water-700' : 'hover:bg-water-700/50'
                    }`
                  }
                >
                  <i className={`fa-solid ${item.icon} w-6 ${item.accent || ''}`}></i>
                  <span className="text-sm font-medium">{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="p-4 border-t border-water-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-red-500 hover:bg-red-600 rounded-lg transition"
          >
            <i className="fa-solid fa-power-off mr-2"></i> End Session
          </button>
        </div>
      </aside>

      {/* ============================================
          MAIN CONTENT AREA
          ============================================ */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
        
        {/* HEADER */}
        <header className="h-16 bg-white shadow-sm flex items-center justify-between px-8 z-10 shrink-0">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-gray-800">{pageTitle}</h2>
            
            {/* Live Connection Indicator */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-gray-50 border border-gray-200" title={connected ? "Live connection active" : "Reconnecting..."}>
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></span>
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wide">
                {connected ? 'Live' : 'Polling'}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative cursor-pointer hover:bg-gray-50 p-2 rounded-full transition">
              <i className="fa-solid fa-bell text-gray-400 text-xl hover:text-water-500"></i>
              <span className="absolute top-1 right-1 bg-red-500 text-white text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center border-2 border-white">
                2
              </span>
            </div>
            
            <div className="h-8 w-px bg-gray-200 mx-2"></div>
            
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-600">
                {displayName} <span className="text-gray-400">({roleLabel})</span>
              </span>
              <div className="w-9 h-9 rounded-full bg-water-100 border border-water-300 flex items-center justify-center text-water-700 font-bold text-sm shadow-sm">
                {initials}
              </div>
            </div>
          </div>
        </header>

        {/* PAGE CONTENT */}
        <div className="p-8 overflow-y-auto overflow-x-hidden flex-1">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </div>
        
      </main>
    </div>
  );
}