import { useEffect, useState } from 'react';
import { alertAPI, taskAPI } from '../services/api';
import { useLiveTelemetry } from '../hooks/useLiveTelemetry';

const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000');

export default function AIAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadAlerts = () => {
    setLoading(true);
    alertAPI
      .list({ is_resolved: false, ordering: '-created_at' })
      .then((res) => setAlerts(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  // Initial load + fallback polling (every 30s)
  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket: Listen for new alerts in real-time
  useLiveTelemetry(`${WS_BASE}/ws/alerts/`, (newAlert) => {
    setAlerts((prev) => {
      // Check if alert already exists to avoid duplicates
      if (prev.some((a) => a.alert_id === newAlert.alert_id)) return prev;
      // Add new alert to the top of the list
      return [newAlert, ...prev];
    });
  });

  // Rename parameter to `item` so it doesn't shadow window.alert
  const handleDeploy = async (item) => {
    try {
      await taskAPI.create({
        pipeline_sector: item.pipeline_sector || item.sector_id, // handles either ID format
        issue_description: `AI-triggered deployment: ${item.message}`,
        priority: item.severity === 'CRITICAL' ? 'CRITICAL' : 'HIGH',
        is_ai_generated: true,
      });
      window.alert('✅ Technician deployment task created successfully');
      loadAlerts();
    } catch (err) {
      window.alert('Failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDismiss = async (id) => {
    try {
      await alertAPI.resolve(id);
      // Remove from UI immediately
      setAlerts((prev) => prev.filter((a) => a.alert_id !== id));
    } catch (err) {
      window.alert('Failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="fade-in">
      <div className="mb-6 flex justify-between items-center">
        <p className="text-gray-600">
          Machine Learning model evaluating real-time pressure drops.
        </p>
        <button
          onClick={loadAlerts}
          className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg shadow-sm hover:bg-gray-50 text-sm font-medium transition flex items-center"
        >
          <i className="fa-solid fa-arrows-rotate mr-2"></i>
          Refresh AI Model
        </button>
      </div>

      {loading && alerts.length === 0 ? (
        <div className="flex justify-center py-12">
          <i className="fa-solid fa-circle-notch fa-spin text-3xl text-water-500"></i>
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <i className="fa-solid fa-circle-check text-5xl text-green-400 mb-4"></i>
          <p className="text-gray-500 text-lg">
            No active alerts. All pipelines operating normally.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((item) => {
            const isCritical = item.severity === 'CRITICAL';
            return (
              <div
                key={item.alert_id}
                className={`border-l-4 rounded-lg shadow-sm p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4 ${
                  isCritical
                    ? 'bg-red-50 border-red-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <div className="flex items-start">
                  <div
                    className={`p-2 rounded-full mr-4 ${
                      isCritical ? 'bg-red-100' : 'bg-yellow-100'
                    }`}
                  >
                    <i
                      className={`fa-solid ${
                        isCritical
                          ? 'fa-triangle-exclamation text-red-600'
                          : 'fa-circle-exclamation text-yellow-600'
                      } text-xl`}
                    ></i>
                  </div>
                  <div>
                    <h4
                      className={`text-lg font-bold ${
                        isCritical ? 'text-red-800' : 'text-yellow-800'
                      }`}
                    >
                      {item.alert_type_display || item.alert_type?.replace('_', ' ')}:{' '}
                      {item.sector_id}
                    </h4>
                    <p
                      className={`text-sm mt-1 ${
                        isCritical ? 'text-red-600' : 'text-yellow-700'
                      }`}
                    >
                      {item.message}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
                      <span
                        className={`px-2 py-1 rounded ${
                          isCritical
                            ? 'bg-red-200 text-red-800'
                            : 'bg-yellow-200 text-yellow-800'
                        }`}
                      >
                        Confidence: {(item.confidence_score * 100).toFixed(0)}%
                      </span>
                      {item.estimated_water_loss && (
                        <span
                          className={`px-2 py-1 rounded ${
                            isCritical
                              ? 'bg-red-200 text-red-800'
                              : 'bg-yellow-200 text-yellow-800'
                          }`}
                        >
                          Est. Water Loss:{' '}
                          {Number(item.estimated_water_loss).toFixed(1)} L/min
                        </span>
                      )}
                      <span
                        className={`px-2 py-1 rounded ${
                          isCritical
                            ? 'bg-red-200 text-red-800'
                            : 'bg-yellow-200 text-yellow-800'
                        }`}
                      >
                        {new Date(item.created_at || Date.now()).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col space-y-2 min-w-45 shrink-0">
                  <button
                    onClick={() => handleDeploy(item)}
                    className={`px-4 py-2 rounded shadow-sm text-sm font-bold text-white ${
                      isCritical
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-yellow-600 hover:bg-yellow-700'
                    }`}
                  >
                    <i className="fa-solid fa-truck-fast mr-2"></i>
                    Deploy Technician
                  </button>
                  <button
                    onClick={() => handleDismiss(item.alert_id)}
                    className={`text-sm font-medium ${
                      isCritical
                        ? 'text-red-700 hover:text-red-900'
                        : 'text-yellow-700 hover:text-yellow-900'
                    }`}
                  >
                    Dismiss Alert
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}