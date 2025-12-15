import React, { useState } from 'react';
import axios from 'axios';
import { Search, Share2, Activity, Database, Zap, Wallet, ChevronRight, Terminal, Layers, Hash } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PersonaChart from './components/PersonaChart';
import RoastCard from './components/RoastCard';
import Logo from './assets/logo.svg';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function StatusCycler() {
  const [msgIndex, setMsgIndex] = useState(0);
  const messages = [
    "> INITIALIZING_NEURAL_UPLINK...",
    "> ESTABLISHING_DUNE_CONNECTION...",
    "> SCANNING_ETHEREUM_HISTORY...",
    "> AGGREGATING_NFT_VECTORS...",
    "> COMPUTING_CLUSTERING_TENSORS...",
    "> DECODING_BEHAVIORAL_PATTERNS...",
    "> FINALIZING_AI_ANALYSIS..."
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex((prev) => (prev + 1) % messages.length);
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex justify-between text-[10px] font-mono text-text-secondary uppercase tracking-widest">
      <span className="animate-pulse">{messages[msgIndex]}</span>
      <span className="animate-pulse">_</span>
    </div>
  );
}

function App() {
  const [wallet, setWallet] = useState("");
  const [status, setStatus] = useState("idle"); 
  const [data, setData] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  
  // ... (rest of code) ...

      {/* Main Content - Flex Layout to avoid scroll */}
      <main className="flex-grow flex flex-col md:flex-row items-center justify-center p-4 md:p-6 overflow-y-auto md:overflow-hidden relative">
        
        {/* Empty / Error State */}
        {(status === 'idle' || status === 'error') && (
          <div className="text-center text-text-secondary space-y-4 max-w-md mt-10 md:mt-0">
            <Layers className={`w-12 h-12 mx-auto ${status === 'error' ? 'text-red-500 opacity-50' : 'opacity-20'}`} />
            <div className="space-y-1">
               <h2 className={`font-medium ${status === 'error' ? 'text-red-400' : 'text-text-primary'}`}>
                 {status === 'error' ? 'System Failure' : 'Ready to Process'}
               </h2>
               <p className="text-xs">
                 {status === 'error' 
                   ? "The neural uplink encountered an error. Check address and retry." 
                   : "Enter a wallet address above to initiate the segmentation engine."}
               </p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {status === 'loading' && (
          <div className="w-64 space-y-2 mt-10 md:mt-0">
            <div className="h-1 bg-border overflow-hidden rounded-full">
              <div className="h-full bg-accent w-1/3 animate-[shimmer_1s_infinite_linear]"></div>
            </div>
            <StatusCycler />
          </div>
        )}

        {/* Dashboard Grid */}
        <AnimatePresence>
          {status === 'success' && data && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-6xl h-auto md:h-full grid grid-cols-1 md:grid-cols-12 gap-4 grid-rows-[auto_1fr] md:grid-rows-1 pb-10 md:pb-0"
            >
              
              {/* Col 1: Visuals (Radar) - 5 Cols */}
              <div className="md:col-span-5 bg-bg-panel border border-border flex flex-col min-h-[350px] md:min-h-0">
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
              <div className="md:col-span-7 flex flex-col gap-4 overflow-visible md:overflow-y-auto pr-1">
                
                {/* Top Row: Metrics */}
                <div className="grid grid-cols-3 gap-2 md:gap-4 h-20 md:h-24 shrink-0">
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

      {/* System Status Footer (Visible only in Idle/Error) */}
      {(status === 'idle' || status === 'error') && (
        <footer className="h-6 bg-bg-panel border-t border-border flex items-center px-4 justify-between text-[10px] font-mono text-text-secondary uppercase shrink-0 z-20">
          <div className="flex gap-4 md:gap-6">
            <span className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${status === 'error' ? 'bg-red-500' : 'bg-green-500'}`}></div>
              {status === 'error' ? 'SYSTEM_OFFLINE' : 'SYSTEM_ONLINE'}
            </span>
            <span className="text-text-primary/70">TARGET: ETH_MAINNET</span>
          </div>
          <div className="flex gap-4">
             <span className="hidden md:block opacity-50">SECURE_UPLINK</span>
             <span className="opacity-50">V2.1.0</span>
          </div>
        </footer>
      )}
    </div>
  );
}

function MetricCard({ label, value, icon }) {
  // Metric display component
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