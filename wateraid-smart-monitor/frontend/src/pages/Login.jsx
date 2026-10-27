import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState('manager');
  const [password, setPassword] = useState('manager123');
  const [role, setRole] = useState('WaterAid Manager');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Invalid credentials. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-water-900 relative overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 opacity-20 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2000&auto=format&fit=crop')",
        }}
      ></div>

      <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md relative z-10 fade-in">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-water-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <i className="fa-solid fa-droplet text-3xl text-water-500"></i>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            WaterAid Smart Monitor
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-based Infrastructure Tracking
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
            <i className="fa-solid fa-circle-exclamation mr-2"></i>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 focus:border-water-500 outline-none"
              placeholder="manager"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 focus:border-water-500 outline-none"
              placeholder="••••••••"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-water-500 focus:border-water-500 outline-none"
            >
              <option>WaterAid Manager</option>
              <option>Field Technician</option>
              <option>System Administrator</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-water-700 hover:bg-water-900 disabled:opacity-60 text-white font-bold py-3 px-4 rounded-lg transition duration-200 flex justify-center items-center"
          >
            {loading ? (
              <>
                <i className="fa-solid fa-circle-notch fa-spin mr-2"></i>
                Signing in...
              </>
            ) : (
              <>
                Secure Login
                <i className="fa-solid fa-arrow-right-to-bracket ml-2"></i>
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-100 text-xs text-gray-400 text-center space-y-1">
          <p>Demo credentials:</p>
          <p>admin / admin123 · manager / manager123 · tech1 / tech123</p>
        </div>
      </div>
    </div>
  );
}