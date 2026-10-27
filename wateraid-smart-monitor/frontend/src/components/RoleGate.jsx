import { useAuth } from '../context/AuthContext';

/**
 * Renders children only if user has one of the allowed roles.
 * Otherwise shows a "no access" panel or redirects.
 */
export function RoleGate({ roles, children, redirect = false }) {
  const { user } = useAuth();
  const allowed = user && roles.includes(user.role_type);

  if (allowed) return children;

  if (redirect) {
    window.location.href = '/dashboard';
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-12 text-center fade-in">
      <i className="fa-solid fa-shield-halved text-5xl text-red-400 mb-4"></i>
      <h2 className="text-xl font-bold text-gray-800 mb-2">Access Restricted</h2>
      <p className="text-gray-500 text-sm">
        Your role (<strong>{user?.role_type}</strong>) does not have permission
        to access this module. Contact your administrator if you believe this
        is an error.
      </p>
    </div>
  );
}

/**
 * Hook that returns permission flags for the current user.
 */
export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role_type;

  return {
    role,
    isAdmin: role === 'ADMIN',
    isManager: role === 'MANAGER',
    isTechnician: role === 'TECHNICIAN',
    isManagerOrAdmin: role === 'MANAGER' || role === 'ADMIN',
    canEditSectors: role === 'MANAGER' || role === 'ADMIN',
    canDeleteUsers: role === 'ADMIN',
    canCreateTasks: !!role, // any authenticated user
    canResolveAlerts: role === 'MANAGER' || role === 'ADMIN',
    canControlSimulator: role === 'MANAGER' || role === 'ADMIN',
  };
}