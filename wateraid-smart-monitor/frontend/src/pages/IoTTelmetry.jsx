import { useEffect, useState, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, LineElement, PointElement, CategoryScale, LinearScale, Filler, Tooltip, Legend,
} from 'chart.js';
import { sectorAPI, sensorLogAPI, simulationAPI } from '../services/api';
import { useLiveTelemetry } from '../hooks/useLiveTelemetry';

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Filler, Tooltip, Legend);

const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000');

export default function IoTTelmetry() {
  const [sectors, setSectors] = useState([]);
  const [selected, setSelected] = useState('');
  const [logs, setLogs] = useState([]);

  // Load sectors once
  useEffect(() => {
    sectorAPI.list().then((res) => {
      const list = res.data.results || res.data;
      setSectors(list);
      if (list.length) setSelected(list[0].sector_id);
    });
  }, []);

  // Full refetch when sector changes
  const loadTrend = () => {
    if (!selected) return;
    sensorLogAPI.trend(selected, 24)
      .then((res) => setLogs(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    loadTrend();
    // Fallback polling every 15s in case WS is down
    const intervalId = setInterval(loadTrend, 15000);
    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  // WebSocket: append real-time data
  const { connected } = useLiveTelemetry(`${WS_BASE}/ws/telemetry/`, (data) => {
    if (!selected || data.sector_id !== selected) return;
    setLogs((prev) => {
      // Append and keep last 500 points
      const next = [...prev, {
        id: data.id,
        pipeline_sector: data.sector_id,
        sector_id: data.sector_id,
        water_flow_rate: data.water_flow_rate,
        water_pressure: data.water_pressure,
        ai_anomaly_flag: data.ai_anomaly_flag,
        timestamp: data.timestamp,
      }];
      return next.slice(-500);
    });
  });

  const handleSimulate = async (scenario) => {
    try {
      await simulationAPI.trigger(selected, scenario);
      // No need to reload — WebSocket will deliver it
    } catch (err) {
      alert('Failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const labels = logs.map((l) =>
    new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  );

  const flowData = {
    labels,
    datasets: [{
      label: 'Flow Rate (L/s)',
      data: logs.map((l) => l.water_flow_rate),
      borderColor: '#0ea5e9',
      backgroundColor: 'rgba(14, 165, 233, 0.1)',
      fill: true, tension: 0.4, pointRadius: 2,
    }],
  };

  const pressureData = {
    labels,
    datasets: [{
      label: 'Pressure (kPa)',
      data: logs.map((l) => l.water_pressure),
      borderColor: '#ef4444',
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
      fill: true, tension: 0.4, pointRadius: 2,
    }],
  };

  const chartOptions = {
    responsive: true, maintainAspectRatio: false, animation: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxRotation: 0 } },
    },
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6 flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-3">
            Live Telemetry Stream
            {connected ? (
              <span className="flex items-center text-xs text-green-600 font-bold bg-green-100 px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                WEBSOCKET LIVE
              </span>
            ) : (
              <span className="flex items-center text-xs text-yellow-600 font-bold bg-yellow-100 px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full mr-1"></span>
                POLLING
              </span>
            )}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Monitoring IoT Sensor node clusters across all regions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <select value={selected} onChange={(e) => setSelected(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-water-500 outline-none max-w-xs">
            {sectors.map((s) => (
              <option key={s.sector_id} value={s.sector_id}>
                {s.sector_id} — {s.location_name}
              </option>
            ))}
          </select>
          <button onClick={() => handleSimulate('normal')}
            className="px-3 py-2 text-xs font-bold rounded-lg bg-green-100 text-green-800 hover:bg-green-200">
            Simulate Normal
          </button>
          <button onClick={() => handleSimulate('pressure_drop')}
            className="px-3 py-2 text-xs font-bold rounded-lg bg-yellow-100 text-yellow-800 hover:bg-yellow-200">
            Simulate Warning
          </button>
          <button onClick={() => handleSimulate('leak')}
            className="px-3 py-2 text-xs font-bold rounded-lg bg-red-100 text-red-800 hover:bg-red-200">
            Simulate Leak
          </button>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-bold text-gray-700">Water Flow Rate (L/s)</h4>
            <span className="flex items-center text-xs text-green-600 font-bold bg-green-100 px-2 py-1 rounded-full">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>LIVE
            </span>
          </div>
          <div className="h-64">
            {logs.length > 0 ? <Line data={flowData} options={chartOptions} /> :
              <div className="h-full flex items-center justify-center text-gray-400">Waiting for telemetry...</div>}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-bold text-gray-700">Pipeline Pressure (kPa)</h4>
            <span className="flex items-center text-xs text-green-600 font-bold bg-green-100 px-2 py-1 rounded-full">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>LIVE
            </span>
          </div>
          <div className="h-64">
            {logs.length > 0 ? <Line data={pressureData} options={chartOptions} /> :
              <div className="h-full flex items-center justify-center text-gray-400">Waiting for telemetry...</div>}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h4 className="font-bold text-gray-700 mb-4">Latest Readings</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2 text-left">Time</th>
                <th className="px-4 py-2 text-right">Flow (L/s)</th>
                <th className="px-4 py-2 text-right">Pressure (kPa)</th>
                <th className="px-4 py-2 text-center">AI Flag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.slice(-10).reverse().map((log, idx) => (
                <tr key={log.id || idx} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-600">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right font-mono">{log.water_flow_rate}</td>
                  <td className="px-4 py-2 text-right font-mono">{log.water_pressure}</td>
                  <td className="px-4 py-2 text-center">
                    {log.ai_anomaly_flag ? (
                      <span className="px-2 py-1 rounded-full bg-red-100 text-red-800 text-xs font-bold">ANOMALY</span>
                    ) : (
                      <span className="px-2 py-1 rounded-full bg-green-100 text-green-800 text-xs font-bold">OK</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}