import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { RoleGate } from './components/RoleGate';
import Login from './pages/Login';
import Layout from './components/Layout';
import ManagerDashboard from './pages/ManagerDashboard';
import TaskEntry from './pages/TaskEntry';
import AIAlerts from './pages/AIAlerts';
import IoTTelmetry from './pages/IoTTelmetry';
import Infrastructure from './pages/Infrastructure';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-water-900">
        <i className="fa-solid fa-circle-notch fa-spin text-4xl text-white"></i>
      </div>
    );
  }
  return user ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<ManagerDashboard />} />

            {/* AI Alerts: managers and admins only */}
            <Route path="ai-alerts" element={
              <RoleGate roles={['MANAGER', 'ADMIN']}>
                <AIAlerts />
              </RoleGate>
            } />

            {/* IoT Telemetry: all authenticated */}
            <Route path="iot-telemetry" element={<IoTTelmetry />} />

            {/* Task Entry: technicians and admins */}
            <Route path="task-entry" element={
              <RoleGate roles={['TECHNICIAN', 'ADMIN', 'MANAGER']}>
                <TaskEntry />
              </RoleGate>
            } />

            {/* Infrastructure: managers and admins */}
            <Route path="infrastructure" element={
              <RoleGate roles={['MANAGER', 'ADMIN']}>
                <Infrastructure />
              </RoleGate>
            } />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;