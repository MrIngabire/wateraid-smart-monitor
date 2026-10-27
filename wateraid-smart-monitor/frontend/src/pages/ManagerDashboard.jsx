import { useEffect, useState } from 'react';
import { Doughnut, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler,
} from 'chart.js';
import { dashboardAPI, sectorAPI, sensorLogAPI } from '../services/api';
import { useLiveTelemetry } from '../hooks/useLiveTelemetry';
const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000');

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler
);

export default function ManagerDashboard() {
  const [stats, setStats] = useState({
    active_pipelines: 0,
    avg_flow_rate: 0,
    active_alerts: 0,
    techs_deployed: 0,
    healthy_sectors: 0,
    warning_sectors: 0,
    critical_sectors: 0,
  });
  const [sectors, setSectors] = useState([]);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([dashboardAPI.stats(), sectorAPI.list({ ordering: 'sector_id' })])
      .then(([s, sec]) => {
        setStats(s.data);
        setSectors(sec.data.results || sec.data);
      })
      .catch((err) => console.error('Dashboard load error', err))
      .finally(() => setLoading(false));
  }, []);

   // Live trend via WebSocket
  
  useEffect(() => {
    if (sectors.length > 0) {
      sensorLogAPI.trend(sectors[0].sector_id, 24)
        .then((res) => setTrend(res.data)).catch(() => {});
    }
  }, [sectors]);

  useLiveTelemetry(`${WS_BASE}/ws/telemetry/`, (data) => {
    // Only update trend for the first sector
    if (sectors.length === 0 || data.sector_id !== sectors[0].sector_id) return;
    setTrend((prev) => [...prev, {
      timestamp: data.timestamp,
      water_flow_rate: data.water_flow_rate,
      water_pressure: data.water_pressure,
    }].slice(-200));
  });

  const healthChartData = {
    labels: ['Optimal', 'Warning', 'Critical'],
    datasets: [
      {
        data: [
          stats.healthy_sectors || 0,
          stats.warning_sectors || 0,
          stats.critical_sectors || 0,
        ],
        backgroundColor: ['#22c55e', '#eab308', '#ef4444'],
        borderWidth: 0,
      },
    ],
  };

  const flowTrendData = {
    labels: trend.slice(-12).map((t) =>
      new Date(t.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    ),
    datasets: [
      {
        label: 'Flow Rate (L/s)',
        data: trend.slice(-12).map((t) => t.water_flow_rate),
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const statCards = [
    {
      label: 'Active Pipelines',
      value: stats.active_pipelines,
      border: 'border-blue-500',
      text: 'text-gray-800',
      bg: '',
    },
    {
      label: 'Avg Flow Rate',
      value: (
        <>
          {stats.avg_flow_rate}{' '}
          <span className="text-lg text-gray-400 font-normal">L/s</span>
        </>
      ),
      border: 'border-water-500',
      text: 'text-gray-800',
      bg: '',
    },
    {
      label: 'AI Leak Alerts',
      value: stats.active_alerts,
      border: 'border-red-500',
      text: 'text-red-700',
      bg: 'bg-red-50',
    },
    {
      label: 'Techs Deployed',
      value: stats.techs_deployed,
      border: 'border-green-500',
      text: 'text-gray-800',
      bg: '',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <i className="fa-solid fa-circle-notch fa-spin text-4xl text-water-500"></i>
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in">
      {/* ============================================
          STAT CARDS
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => (
          <div
            key={card.label}
            className={`bg-white rounded-xl shadow-sm p-6 border-l-4 ${card.border} ${card.bg}`}
          >
            <p
              className={`text-sm font-medium uppercase tracking-wide ${
                card.bg ? 'text-red-500' : 'text-gray-500'
              }`}
            >
              {card.label}
            </p>
            <p className={`text-3xl font-bold mt-2 ${card.text}`}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* ============================================
          ROW 2 — MAP + DOUGHNUT
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map panel */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">
            Regional Infrastructure Status
          </h3>

          <div className="h-64 rounded-lg bg-linear-to-br from-water-50 via-gray-50 to-water-100 relative overflow-hidden border border-gray-100">
            <div className="absolute inset-0 opacity-40">
              <svg
                className="w-full h-full"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 800 400"
                preserveAspectRatio="xMidYMid slice"
              >
                <path
                  d="M0,200 Q200,180 400,220 T800,200"
                  stroke="#0ea5e9"
                  strokeWidth="1.5"
                  fill="none"
                  opacity="0.5"
                />
                <path
                  d="M100,0 Q150,200 200,400"
                  stroke="#94a3b8"
                  strokeWidth="1"
                  fill="none"
                  opacity="0.3"
                />
                <path
                  d="M500,0 Q550,200 600,400"
                  stroke="#94a3b8"
                  strokeWidth="1"
                  fill="none"
                  opacity="0.3"
                />
                <circle cx="200" cy="180" r="4" fill="#22c55e" />
                <circle cx="400" cy="220" r="4" fill="#ef4444" />
                <circle cx="600" cy="200" r="4" fill="#eab308" />
              </svg>
            </div>

            <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
              <i className="fa-solid fa-map-location-dot text-4xl text-water-400 mb-2"></i>
              <p className="text-gray-500 font-medium">Interactive GIS Map</p>
              <p className="text-xs text-gray-400 mt-1">
                {sectors.length} sectors registered across Rwanda
              </p>
            </div>

            <div className="absolute top-4 right-4 flex items-center gap-3 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1.5 text-xs font-semibold shadow-sm">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                {stats.healthy_sectors}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                {stats.warning_sectors}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                {stats.critical_sectors}
              </span>
            </div>
          </div>
        </div>

        {/* Doughnut chart — legend on right, no center text */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">
            Pipeline Health Overview
          </h3>
          <div className="relative h-48">
            <Doughnut
              data={healthChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'right',
                    labels: {
                      font: { size: 12 },
                      usePointStyle: false,
                      boxWidth: 12,
                      padding: 12,
                    },
                  },
                },
                cutout: '70%',
              }}
            />
          </div>
        </div>
      </div>

      {/* ============================================
          ROW 3 — TREND
          ============================================ */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-800">
            Real-Time Flow Rate Trend (Last 24h)
          </h3>
          <span className="flex items-center text-xs text-green-600 font-bold bg-green-100 px-2 py-1 rounded-full">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
            LIVE
          </span>
        </div>
        <div className="h-64">
          {trend.length > 0 ? (
            <Line
              data={flowTrendData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  y: {
                    beginAtZero: false,
                    grid: { color: '#f1f5f9' },
                    ticks: { color: '#94a3b8' },
                  },
                  x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' },
                  },
                },
              }}
            />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <i className="fa-solid fa-chart-line text-4xl mb-2"></i>
              <p>No telemetry data available yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}