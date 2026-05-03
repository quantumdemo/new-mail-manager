import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import { Mail, ShieldCheck, Sparkles, AlertCircle, AlertTriangle, Loader2, RefreshCw, Sun, Moon, Database, TrendingDown, Trash2, Info, Filter, ArrowUpDown, X, ShieldAlert, Calendar } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Global axios config to ensure cookies (sessions) are passed
axios.defaults.withCredentials = true;

// --- Components ---

const ThemeToggle = () => {
  const [isDark, setIsDark] = useState(() => localStorage.getItem('theme') === 'dark');
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);
  return (
    <button onClick={() => setIsDark(!isDark)} className="p-2 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
      {isDark ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-indigo-600" />}
    </button>
  );
};

const Layout = ({ children }) => (
  <div className="min-h-screen flex flex-col bg-white dark:bg-[#121212] text-gray-900 dark:text-gray-100 transition-colors duration-200">
    <header className="bg-white dark:bg-[#121212] border-b border-gray-200 dark:border-gray-800 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#3f51b5] rounded-lg flex items-center justify-center text-white font-bold">M</div>
          <h1 className="text-xl font-bold hidden sm:block">Mail Manager</h1>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
        </div>
      </div>
    </header>
    <main className="flex-grow max-w-7xl mx-auto w-full px-4 py-8">{children}</main>
    <footer className="bg-gray-50 dark:bg-black py-6 border-t border-gray-200 dark:border-gray-800 text-center text-sm text-gray-500">
      <p>© 2026 Mail Manager - Privacy-first email cleanup. No data is stored.</p>
    </footer>
  </div>
);

const StatCard = ({ title, value, icon: Icon, description, colorClass }) => (
  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
    <div className="flex items-center justify-between mb-4">
      <div className={`p-3 rounded-lg ${colorClass}`}><Icon className="w-6 h-6 text-white" /></div>
      <span className="text-2xl font-bold">{value}</span>
    </div>
    <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">{title}</h3>
    <p className="text-xs text-gray-400 mt-1">{description}</p>
  </motion.div>
);

const Dashboard = ({ stats }) => {
  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024; const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  const potentialSavings = stats.senders.filter(s => s.recommendation === 'safe').reduce((acc, s) => acc + s.total_size, 0);
  return (
    <div className="space-y-6">
      <p className="text-[10px] text-gray-400 italic">* All storage values are estimates based on metadata analysis.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Scanned" value={stats.total_scanned} icon={Mail} description="Emails in range" colorClass="bg-blue-500" />
        <StatCard title="Est. Storage" value={formatSize(stats.total_estimated_size)} icon={Database} description="Total space occupied" colorClass="bg-gray-600" />
        <StatCard title="Potential Savings" value={formatSize(potentialSavings)} icon={TrendingDown} description="Safe for cleanup" colorClass="bg-teal-500" />
        <StatCard title="Safe Senders" value={stats.senders.filter(s => s.recommendation === 'safe').length} icon={ShieldCheck} description="AI Recommended" colorClass="bg-green-500" />
      </div>
    </div>
  );
};

const DeletionDialog = ({ isOpen, sender, onConfirm, onCancel, isDeleting, isBulk = false }) => {
  const [doubleConfirm, setDoubleConfirm] = useState(false);
  if (!isOpen || !sender) return null;

  const getCount = () => {
    if (isBulk) return sender.reduce((acc, s) => acc + s.count, 0);
    return sender.count;
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onCancel} className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="relative w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl p-6 shadow-2xl">
          <div className={`w-12 h-12 rounded-full ${doubleConfirm ? 'bg-red-500 animate-pulse' : 'bg-red-100'} flex items-center justify-center mb-4`}>
            {doubleConfirm ? <ShieldAlert className="w-6 h-6 text-white" /> : <AlertTriangle className="w-6 h-6 text-red-600" />}
          </div>
          <h3 className="text-xl font-bold mb-2">{doubleConfirm ? 'Are you absolutely sure?' : (isBulk ? 'Bulk Delete Recommended?' : 'Delete Emails?')}</h3>
          <p className="text-gray-500 mb-6">{doubleConfirm ? `This will move ${getCount()} emails to the trash. This action is reversible from your trash folder.` : (isBulk ? `This will clean ${getCount()} emails from all senders identified as safe.` : `This will move ${getCount()} emails from ${sender.sender} to the trash.`)}</p>
          <div className="flex gap-3">
            <button disabled={isDeleting} onClick={() => doubleConfirm ? onConfirm() : setDoubleConfirm(true)} className={`flex-1 ${doubleConfirm ? 'bg-red-700' : 'bg-red-600'} text-white font-bold py-3 rounded-xl transition-all`}>{isDeleting ? 'Processing...' : 'Confirm'}</button>
            <button onClick={onCancel} className="flex-1 bg-gray-100 dark:bg-gray-800 font-bold py-3 rounded-xl">Cancel</button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

// --- Main App ---

export default function App() {
  const [sessionId, setSessionId] = useState(sessionStorage.getItem('session_id'));
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scanProgress, setScanProgress] = useState(null);
  const [senderToDelete, setSenderToDelete] = useState(null);
  const [isBulkDelete, setIsBulkDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState(null);

  const startScan = useCallback(async (sid) => {
    setLoading(true); setScanProgress({ current: 0, total: 1000 }); setError(null);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/scan`, { session_id: sid });
      setStats(res.data);
    } catch (e) {
      console.error(e);
      setError("Failed to scan inbox. Please ensure your session hasn't expired.");
    } finally { setLoading(false); setScanProgress(null); }
  }, []);

  useEffect(() => {
    const s = io(API_BASE_URL);
    if (sessionId) s.emit('join', { session_id: sessionId });
    s.on('scan_progress', data => setScanProgress(data));
    const handleMsg = e => {
      if (e.data.type === 'AUTH_SUCCESS') {
        setSessionId(e.data.session_id); sessionStorage.setItem('session_id', e.data.session_id);
        s.emit('join', { session_id: e.data.session_id }); startScan(e.data.session_id);
      }
    };
    window.addEventListener('message', handleMsg);
    return () => { window.removeEventListener('message', handleMsg); s.close(); };
  }, [sessionId, startScan]);

  const handleLogin = async () => {
    setError(null);
    try {
      const res = await axios.get(`${API_BASE_URL}/auth/google/login`);
      window.open(res.data.url, '_blank', 'width=600,height=600');
    } catch (e) {
      setError("Failed to initiate login. Please try again.");
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const ids = isBulkDelete ? senderToDelete.flatMap(s => s.all_ids) : senderToDelete.all_ids;
      await axios.post(`${API_BASE_URL}/api/delete`, { session_id: sessionId, email_ids: ids });
      await startScan(sessionId); setSenderToDelete(null); setIsBulkDelete(false);
    } catch (e) { console.error(e); } finally { setIsDeleting(false); }
  };

  if (!sessionId) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto py-20 text-center">
          <h2 className="text-5xl font-extrabold mb-6">Clean Inbox. <span className="text-[#3f51b5]">Free Space.</span></h2>
          <p className="text-xl text-gray-500 mb-12">The privacy-first Gmail cleaner. No data stored. No persistent tokens.</p>
          <button onClick={handleLogin} className="bg-[#3f51b5] text-white p-4 rounded-xl font-bold flex items-center gap-2 mx-auto shadow-lg hover:opacity-90">
             Connect Gmail
          </button>
          {error && <p className="mt-4 text-red-500 font-medium">{error}</p>}
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Analysis Results</h2>
          <div className="flex gap-4">
            <button onClick={() => startScan(sessionId)} className="bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg font-medium">Refresh</button>
            <button onClick={() => { axios.post(`${API_BASE_URL}/auth/logout`, { session_id: sessionId }); setSessionId(null); sessionStorage.removeItem('session_id'); }} className="text-red-500 font-medium">Logout</button>
          </div>
        </div>
        {loading ? (
          <div className="flex flex-col items-center py-20 gap-4">
            <Loader2 className="w-12 h-12 animate-spin text-[#3f51b5]" />
            <p className="font-bold">Scanning... {scanProgress ? `${scanProgress.current} emails` : ''}</p>
          </div>
        ) : stats && (
          <>
            <Dashboard stats={stats} />
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 overflow-hidden">
               <div className="p-4 border-b dark:border-gray-700 flex justify-between items-center">
                  <h3 className="font-bold">Senders</h3>
                  {stats.senders.filter(s => s.recommendation === 'safe').length > 0 && (
                    <button onClick={() => { setSenderToDelete(stats.senders.filter(s => s.recommendation === 'safe')); setIsBulkDelete(true); }} className="bg-teal-500 text-white text-xs px-3 py-1.5 rounded-full font-bold flex items-center gap-1"><Sparkles className="w-3 h-3" /> Quick Clean</button>
                  )}
               </div>
               <div className="overflow-x-auto">
                 <table className="w-full text-left">
                   <thead className="bg-gray-50 dark:bg-gray-900 text-xs uppercase text-gray-400">
                     <tr><th className="px-6 py-4">Sender</th><th className="px-6 py-4 text-center">Emails</th><th className="px-6 py-4 text-center">Size</th><th className="px-6 py-4 text-center">Action</th></tr>
                   </thead>
                   <tbody className="divide-y dark:divide-gray-700">
                     {stats.senders.map(s => (
                       <tr key={s.sender} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                         <td className="px-6 py-4">
                           <div className="text-sm font-medium">{s.sender}</div>
                           <div className="text-xs text-gray-400">{s.explanation}</div>
                         </td>
                         <td className="px-6 py-4 text-center text-sm">{s.count}</td>
                         <td className="px-6 py-4 text-center text-sm">{Math.round(s.total_size/1024)} KB</td>
                         <td className="px-6 py-4 text-center">
                           <button onClick={() => { setSenderToDelete(s); setIsBulkDelete(false); }} className="text-red-500 p-2 hover:bg-red-900/20 rounded-full"><Trash2 className="w-4 h-4" /></button>
                         </td>
                       </tr>
                     ))}
                   </tbody>
                 </table>
               </div>
            </div>
          </>
        )}
        {error && <p className="text-red-500 text-center font-medium">{error}</p>}
      </div>
      <DeletionDialog isOpen={!!senderToDelete} sender={senderToDelete} isBulk={isBulkDelete} onConfirm={handleDelete} onCancel={() => setSenderToDelete(null)} isDeleting={isDeleting} />
    </Layout>
  );
}
