import { useEffect, useState } from 'react';
import { sectorAPI } from '../services/api';

export default function Infrastructure() {
  const [sectors, setSectors] = useState([]);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    sector_id: '',
    location_name: '',
    region: '',
    installation_date: new Date().toISOString().split('T')[0],
    pipeline_length_km: 0,
  });

  const loadSectors = () => {
    sectorAPI.list().then((res) => setSectors(res.data.results || res.data));
  };

  useEffect(loadSectors, []);

  const filtered = sectors.filter(
    (s) =>
      s.sector_id.toLowerCase().includes(search.toLowerCase()) ||
      s.location_name.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await sectorAPI.create(form);
      setShowModal(false);
      setForm({
        sector_id: '',
        location_name: '',
        region: '',
        installation_date: new Date().toISOString().split('T')[0],
        pipeline_length_km: 0,
      });
      loadSectors();
    } catch (err) {
      alert('Error: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  const statusBadge = (status) => {
    const map = {
      ACTIVE: 'bg-green-100 text-green-800',
      AI_ALERT: 'bg-red-100 text-red-800',
      MAINTENANCE: 'bg-yellow-100 text-yellow-800',
      OFFLINE: 'bg-gray-200 text-gray-700',
    };
    return map[status] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="fade-in">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div className="relative w-full md:w-72">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-water-500"
            placeholder="Search infrastructure ID..."
          />
          <i className="fa-solid fa-magnifying-glass absolute left-3 top-3 text-gray-400"></i>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-water-700 text-white px-4 py-2 rounded-lg shadow-sm hover:bg-water-800 transition flex items-center"
        >
          <i className="fa-solid fa-plus mr-2"></i>
          Register New Sector
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {[
                  'Sector ID',
                  'Location',
                  'IoT Sensor IP',
                  'Install Date',
                  'Status',
                  'Action',
                ].map((h, idx) => (
                  <th
                    key={h}
                    className={`px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider ${
                      idx === 5 ? 'text-right' : 'text-left'
                    }`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200 text-sm">
              {filtered.map((s, i) => (
                <tr key={s.sector_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-mono font-bold text-gray-900">
                    {s.sector_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                    {s.location_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500 font-mono">
                    {s.sensor_ip || (
                      <span className="text-gray-400 italic">Not Assigned</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {new Date(s.installation_date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: '2-digit',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-bold rounded-full ${statusBadge(
                        s.status
                      )}`}
                    >
                      {s.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                    {s.sensor_ip ? (
                      <button className="text-water-600 hover:text-water-900">
                        <i className="fa-solid fa-gear"></i> Config
                      </button>
                    ) : (
                      <button className="text-water-600 hover:text-water-900">
                        <i className="fa-solid fa-link"></i> Bind Sensor
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-gray-400">
                    No sectors found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md fade-in">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
              <h3 className="font-bold text-lg">Register New Sector</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-700"
              >
                <i className="fa-solid fa-xmark text-xl"></i>
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              {[
                { label: 'Sector ID', key: 'sector_id', placeholder: 'SEC-XXX-00' },
                { label: 'Location Name', key: 'location_name', placeholder: 'e.g. Nyanza Central' },
                { label: 'Region', key: 'region', placeholder: 'e.g. Nyanza' },
                { label: 'Installation Date', key: 'installation_date', type: 'date' },
                { label: 'Pipeline Length (km)', key: 'pipeline_length_km', type: 'number' },
              ].map((field) => (
                <div key={field.key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.label}
                  </label>
                  <input
                    type={field.type || 'text'}
                    value={form[field.key]}
                    onChange={(e) =>
                      setForm({ ...form, [field.key]: e.target.value })
                    }
                    placeholder={field.placeholder}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 outline-none"
                    required
                  />
                </div>
              ))}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-water-700 text-white px-6 py-2 rounded-lg hover:bg-water-800"
                >
                  Create Sector
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}