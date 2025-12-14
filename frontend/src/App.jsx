import React, { useState } from 'react';
import axios from 'axios';
import { Search, Share2, Activity, Database, Zap, Wallet, ChevronRight, Terminal, Layers, Hash } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PersonaChart from './components/PersonaChart';
import RoastCard from './components/RoastCard';
import Logo from './assets/logo.svg';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [wallet, setWallet] = useState("");
  const [status, setStatus] = useState("idle"); 
  const [data, setData] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const analyzeWallet = async () => {
    if (!wallet.startsWith("0x")) {
      setErrorMsg("INVALID_ADDRESS: Must start with 0x");
      return;
    }
    
    setStatus("loading");
    setErrorMsg("");
    setData(null);

    try {
      const startRes = await axios.post(`${API_BASE}/analyze/start/${wallet}`);
      pollStatus(startRes.data.job_id);
    } catch (err) {
      console.error(err);
      setErrorMsg("CONNECTION_ERR: API Unreachable");
      setStatus("error");
    }
  };

  const pollStatus = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/analyze/status/${jobId}`);
        const result = res.data;
        
        if (result.status === "completed") {
          clearInterval(interval);
          setData(result);
          setStatus("success");
        } else if (result.status === "failed") {
          clearInterval(interval);
          setErrorMsg(result.error || "Analysis Failed");
          setStatus("error");
        }
      } catch (err) {
        clearInterval(interval);
        setErrorMsg("POLLING_ERR: Lost connection");
        setStatus("error");
      }
    }, 2000);
  };

  const handleExport = () => {
    if (!data) return;
    const jsonString = `data:text/json;chatset=utf-8,${encodeURIComponent(
      JSON.stringify(data, null, 2)
    )}`;
    const link = document.createElement("a");
    link.href = jsonString;
    link.download = `analysis_${data.wallet_address || "wallet"}.json`;
    link.click();
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-bg-main text-sm">
      
      {/* 1. Compact Top Navigation Bar */}
      <header className="h-14 border-b border-border bg-bg-panel flex items-center px-4 justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 text-accent flex items-center justify-center">
             <img src={Logo} alt="Cluster Protocol" className="w-full h-full text-accent" />
          </div>
          <h1 className="font-mono font-semibold tracking-tight text-text-primary">
            CLUSTER<span className="text-text-secondary">PROTOCOL</span>
          </h1>
          <span className="px-2 py-0.5 rounded-full bg-border text-[10px] text-text-secondary font-mono">v2.1.0</span>
        </div>

        {/* Dense Search Input */}
        <div className="flex items-center gap-2 w-full max-w-md">
          <div className="relative flex-grow group">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary">
              <Terminal size={14} />
            </div>
            <input
              type="text"
              value={wallet}
              onChange={(e) => setWallet(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && analyzeWallet()}
              placeholder="0x..."
              className="w-full bg-bg-main border border-border text-text-primary pl-9 pr-3 py-1.5 font-mono text-xs focus:outline-none focus:border-accent transition-colors rounded-sm"
              disabled={status === 'loading'}
            />
          </div>
          <button
            onClick={analyzeWallet}
            disabled={status === 'loading'}
            className="px-4 py-1.5 bg-accent hover:bg-amber-400 text-black font-semibold text-xs uppercase tracking-wide rounded-sm transition-colors disabled:opacity-50"
          >
            {status === 'loading' ? "RUNNING..." : "EXECUTE"}
          </button>
        </div>
      </header>
      
      {/* Error Toast */}
      {errorMsg && (
        <div className="bg-red-900/20 border-b border-red-900/50 text-red-400 px-4 py-2 text-xs font-mono text-center">
          ! {errorMsg}
        </div>
      )}

      {/* Main Content - Flex Layout to avoid scroll */}
      <main className="flex-grow flex items-center justify-center p-4 md:p-6 overflow-hidden relative">
        
        {/* Empty State */}
        {status === 'idle' && (
          <div className="text-center text-text-secondary space-y-4 max-w-md">
            <Layers className="w-12 h-12 mx-auto opacity-20" />
            <div className="space-y-1">
               <h2 className="text-text-primary font-medium">Ready to Process</h2>
               <p className="text-xs">Enter a wallet address above to initiate the segmentation engine.</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {status === 'loading' && (
          <div className="w-64 space-y-2">
            <div className="h-1 bg-border overflow-hidden rounded-full">
              <div className="h-full bg-accent w-1/3 animate-[shimmer_1s_infinite_linear]"></div>
            </div>
            <div className="flex justify-between text-[10px] font-mono text-text-secondary uppercase">
              <span>Ingesting Data</span>
              <span className="animate-pulse">...</span>
            </div>
          </div>
        )}

        {/* Dashboard Grid */}
        <AnimatePresence>
          {status === 'success' && data && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-6xl h-full grid grid-cols-1 md:grid-cols-12 gap-4 grid-rows-[auto_1fr] md:grid-rows-1"
            >
              
              {/* Col 1: Visuals (Radar) - 5 Cols */}
              <div className="md:col-span-5 bg-bg-panel border border-border flex flex-col">
                <div className="p-3 border-b border-border flex justify-between items-center">
                  <span className="text-xs font-mono text-text-primary font-semibold uppercase tracking-wider">Behavioral Topology</span>
                  <Activity size={12} className="text-text-secondary" />
                </div>
                <div className="flex-grow min-h-[250px] relative p-4">
                  <PersonaChart scores={data.confidence_scores} />
                </div>
                <div className="p-3 border-t border-border bg-bg-main">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-text-secondary">Primary Classification</span>
                    <span className="text-accent text-xs font-mono font-bold">{data.persona}</span>
                  </div>
                  <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-accent" 
                      style={{ width: `${Math.max(...Object.values(data.confidence_scores)) * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Col 2: Metrics & Insights - 7 Cols */}
              <div className="md:col-span-7 flex flex-col gap-4 overflow-y-auto pr-1">
                
                {/* Top Row: Metrics */}
                <div className="grid grid-cols-3 gap-4 h-24 shrink-0">
                  <MetricCard 
                    label="TX_COUNT" 
                    value={data.stats.tx_count} 
                    icon={<Hash size={14} />} 
                  />
                  <MetricCard 
                    label="NFT_VAL_USD" 
                    value={`$${Math.round(data.stats.total_nft_volume_usd).toLocaleString()}`} 
                    icon={<Database size={14} />} 
                  />
                  <MetricCard 
                    label="GAS_ETH" 
                    value={data.stats.total_gas_spent.toFixed(4)} 
                    icon={<Zap size={14} />} 
                  />
                </div>

                {/* Bottom Row: Text Analysis */}
                <div className="flex-grow bg-bg-panel border border-border flex flex-col">
                  <div className="p-3 border-b border-border flex justify-between items-center bg-bg-main/50">
                    <span className="text-xs font-mono text-text-primary font-semibold uppercase tracking-wider">Identity Narrative</span>
                    <div className="flex gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500/20 border border-red-500/50"></div>
                      <div className="w-2 h-2 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
                      <div className="w-2 h-2 rounded-full bg-green-500/20 border border-green-500/50"></div>
                    </div>
                  </div>
                  <div className="p-0 flex-grow relative overflow-hidden">
                     <RoastCard explanation={data.explanation} />
                  </div>
                  <div className="p-3 border-t border-border flex justify-between items-center">
                    <button 
                      onClick={handleExport}
                      className="flex items-center gap-2 text-xs text-text-secondary hover:text-white transition-colors"
                    >
                      <Share2 size={12} />
                      <span>EXPORT_JSON</span>
                    </button>
                    <span className="text-[10px] text-text-secondary font-mono">LATENCY: 42ms</span>
                  </div>
                </div>

              </div>

            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

function MetricCard({ label, value, icon }) {
  return (
    <div className="bg-bg-panel border border-border p-3 flex flex-col justify-between">
      <div className="flex justify-between items-start text-text-secondary">
        <span className="text-[10px] font-mono tracking-wider">{label}</span>
        {icon}
      </div>
      <div className="text-lg font-semibold text-text-primary tracking-tight font-mono">
        {value}
      </div>
    </div>
  );
}

export default App;