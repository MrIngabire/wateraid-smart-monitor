import { useEffect, useState } from 'react';
import { sectorAPI, taskAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function TaskEntry() {
  const { user } = useAuth();
  const [sectors, setSectors] = useState([]);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    pipeline_sector: '',
    issue_description: '',
    parts_replaced: '',
    is_resolved: false,
    priority: 'MEDIUM',
  });

  useEffect(() => {
    sectorAPI
      .list()
      .then((res) => {
        const list = res.data.results || res.data;
        setSectors(list);
        if (list.length) setForm((f) => ({ ...f, pipeline_sector: list[0].sector_id }));
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await taskAPI.create({
        pipeline_sector: form.pipeline_sector,
        issue_description: form.issue_description,
        parts_replaced: form.parts_replaced,
        status: form.is_resolved ? 'RESOLVED' : 'PENDING',
        priority: form.priority,
      });
      setSubmitted(true);
      setForm({
        pipeline_sector: sectors[0]?.sector_id || '',
        issue_description: '',
        parts_replaced: '',
        is_resolved: false,
        priority: 'MEDIUM',
      });
      setTimeout(() => setSubmitted(false), 4000);
    } catch (err) {
      alert('Failed to submit: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="max-w-2xl mx-auto fade-in">
      {submitted && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg flex items-center">
          <i className="fa-solid fa-circle-check mr-3 text-lg"></i>
          Task successfully logged to the database!
        </div>
      )}

      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="bg-water-700 px-6 py-4">
          <h3 className="text-lg font-bold text-white flex items-center">
            <i className="fa-solid fa-clipboard-check mr-2"></i>
            Maintenance Task Entry
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pipeline Sector ID
              </label>
              <select
                value={form.pipeline_sector}
                onChange={(e) =>
                  setForm({ ...form, pipeline_sector: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 outline-none"
                required
              >
                {sectors.map((s) => (
                  <option key={s.sector_id} value={s.sector_id}>
                    {s.sector_id} — {s.location_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 outline-none"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Issue Description &amp; Repairs Made
            </label>
            <textarea
              rows="4"
              value={form.issue_description}
              onChange={(e) =>
                setForm({ ...form, issue_description: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 outline-none"
              placeholder="Detail the leak location, cause, and actions taken..."
              required
            ></textarea>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Parts Replaced
            </label>
            <input
              type="text"
              value={form.parts_replaced}
              onChange={(e) =>
                setForm({ ...form, parts_replaced: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 outline-none"
              placeholder="e.g., 2x PVC Joints, 1x Pressure Valve"
            />
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-gray-100">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="resolved"
                checked={form.is_resolved}
                onChange={(e) =>
                  setForm({ ...form, is_resolved: e.target.checked })
                }
                className="h-4 w-4 text-water-600 focus:ring-water-500 border-gray-300 rounded"
              />
              <label
                htmlFor="resolved"
                className="ml-2 block text-sm text-gray-900 font-medium"
              >
                Issue Fully Resolved
              </label>
            </div>

            <button
              type="submit"
              className="bg-water-600 hover:bg-water-700 text-white font-bold py-2 px-6 rounded-lg shadow-sm transition"
            >
              <i className="fa-solid fa-paper-plane mr-2"></i>
              Submit Log
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}