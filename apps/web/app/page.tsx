'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bot,
  Brain,
  CheckCircle2,
  ChevronRight,
  Cpu,
  DollarSign,
  FileText,
  Flame,
  Layers,
  Lock,
  PieChart,
  Play,
  RefreshCw,
  Scale,
  Shield,
  ShieldAlert,
  Sliders,
  TrendingDown,
  TrendingUp,
  Workflow,
  Zap,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPie,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'markets' | 'agents' | 'strategies' | 'debate' | 'risk' | 'portfolio' | 'execution' | 'backtest' | 'journal' | 'learning'>('overview');
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<any>(null);
  const [optimizerObjective, setOptimizerObjective] = useState('MAX_SHARPE');

  // Simulated live state
  const [nav, setNav] = useState(104850.20);
  const [dailyPnl, setDailyPnl] = useState(1450.30);
  const [dailyPnlPct, setDailyPnlPct] = useState(1.40);
  const [regime, setRegime] = useState('SIDEWAYS');
  const [regimeConf, setRegimeConf] = useState(78);

  const equityData = [
    { time: '09:30', nav: 100000 },
    { time: '10:00', nav: 100450 },
    { time: '10:30', nav: 101200 },
    { time: '11:00', nav: 100950 },
    { time: '11:30', nav: 101800 },
    { time: '12:00', nav: 102400 },
    { time: '12:30', nav: 102150 },
    { time: '13:00', nav: 103100 },
    { time: '13:30', nav: 103850 },
    { time: '14:00', nav: 104200 },
    { time: '14:30', nav: 103900 },
    { time: '15:00', nav: 104500 },
    { time: '15:30', nav: 104850 },
  ];

  const candleData = [
    { date: 'Aug 18', open: 220.1, high: 224.5, low: 219.0, close: 223.8, volume: 45000000, ema50: 218.4, ema200: 205.1 },
    { date: 'Aug 19', open: 223.5, high: 226.2, low: 222.8, close: 225.4, volume: 52000000, ema50: 219.2, ema200: 205.6 },
    { date: 'Aug 20', open: 225.8, high: 228.0, low: 224.1, close: 227.1, volume: 61000000, ema50: 220.1, ema200: 206.1 },
    { date: 'Aug 21', open: 226.5, high: 227.4, low: 223.5, close: 224.2, volume: 48000000, ema50: 220.8, ema200: 206.5 },
    { date: 'Aug 22', open: 224.0, high: 226.8, low: 223.0, close: 226.0, volume: 41000000, ema50: 221.4, ema200: 207.0 },
    { date: 'Aug 25', open: 226.5, high: 230.2, low: 225.8, close: 229.5, volume: 68000000, ema50: 222.3, ema200: 207.5 },
    { date: 'Aug 26', open: 229.8, high: 232.0, low: 228.4, close: 231.4, volume: 74000000, ema50: 223.4, ema200: 208.1 },
    { date: 'Aug 27', open: 231.0, high: 233.5, low: 230.1, close: 232.8, volume: 62000000, ema50: 224.5, ema200: 208.7 },
    { date: 'Aug 28', open: 233.0, high: 235.1, low: 231.8, close: 234.6, volume: 81000000, ema50: 225.8, ema200: 209.3 },
    { date: 'Aug 29', open: 234.5, high: 236.4, low: 233.2, close: 235.9, volume: 79000000, ema50: 227.1, ema200: 210.0 },
  ];

  const agentList = [
    { id: 'technical', name: 'Technical Agent', signal: 'BUY', conf: 84, latency: 12, ret: '+4.5%', risk: '1.8%', reason: 'EMA 9 > 21 golden alignment with RSI 58 momentum expansion.' },
    { id: 'quant', name: 'Quant Agent', signal: 'BUY', conf: 88, latency: 8, ret: '+4.2%', risk: '1.4%', reason: 'Annualized alpha 4.5%, Sharpe 1.85, positive Z-score mean reversion.' },
    { id: 'fundamental', name: 'Fundamental Agent', signal: 'BUY', conf: 80, latency: 18, ret: '+6.0%', risk: '2.5%', reason: 'High quality ROE (28%), accelerating datacenter revenue.' },
    { id: 'sentiment', name: 'Sentiment Agent', signal: 'BUY', conf: 76, latency: 45, ret: '+3.5%', risk: '2.0%', reason: 'FinBERT score +0.35, 68% bullish retail/institutional consensus.' },
    { id: 'macro', name: 'Macro Agent', signal: 'BUY', conf: 78, latency: 22, ret: '+3.0%', risk: '1.5%', reason: 'Risk-on macro score 0.72, VIX low at 14.8, sovereign yields stable.' },
    { id: 'microstructure', name: 'Microstructure Agent', signal: 'BUY', conf: 82, latency: 5, ret: '+2.0%', risk: '1.0%', reason: 'Order book imbalance +12% on bid depth, spread 3.5 bps.' },
    { id: 'options', name: 'Options Agent', signal: 'BUY', conf: 81, latency: 14, ret: '+4.0%', risk: '2.0%', reason: 'Put/Call ratio 0.82, positive dealer gamma pin damping downside.' },
    { id: 'cross_asset', name: 'Cross-Asset Agent', signal: 'BUY', conf: 79, latency: 10, ret: '+3.0%', risk: '1.5%', reason: 'SPY, QQQ, and BTC co-movement confirming risk appetite.' },
    { id: 'pattern_discovery', name: 'Pattern Discovery', signal: 'BUY', conf: 75, latency: 15, ret: '+3.8%', risk: '1.8%', reason: 'Ascending consolidation triangle breakout with volume surge.' },
    { id: 'simulation', name: 'Simulation Agent', signal: 'BUY', conf: 85, latency: 32, ret: '+4.2%', risk: '1.9%', reason: '1,000 Monte Carlo forward paths yield 71.4% win probability.' },
    { id: 'data_quality', name: 'Data Quality Agent', signal: 'PASS', conf: 99, latency: 2, ret: '0.0%', risk: '0.0%', reason: 'Data Quality Score 0.98/1.0. Zero timestamp or tick anomalies.' },
    { id: 'compliance', name: 'Compliance Agent', signal: 'PASS', conf: 100, latency: 1, ret: '0.0%', risk: '0.0%', reason: 'No wash-sale restrictions, symbol verified in universe, leverage 1.0x.' },
    { id: 'cost_analysis', name: 'Cost Analysis Agent', signal: 'PASS', conf: 96, latency: 3, ret: '-0.05%', risk: '0.0%', reason: 'Roundtrip execution drag estimated at 4.5 bps (minimal drag).' },
    { id: 'research', name: 'Research Agent', signal: 'BUY', conf: 83, latency: 55, ret: '+5.0%', risk: '2.0%', reason: 'Solid structural moat, positive earnings revisions, patent tailwinds.' },
  ];

  const strategyList = [
    { name: 'Trend Following', signal: 'BUY', conf: 82, ret: '5.5%', dd: '2.2%', period: '10D', sharpe: 1.65 },
    { name: 'Momentum Acceleration', signal: 'BUY', conf: 80, ret: '4.8%', dd: '2.0%', period: '5D', sharpe: 1.55 },
    { name: 'Mean Reversion', signal: 'HOLD', conf: 50, ret: '3.5%', dd: '1.5%', period: '3D', sharpe: 1.40 },
    { name: 'Swing Support/Resistance', signal: 'BUY', conf: 76, ret: '4.2%', dd: '1.8%', period: '5D', sharpe: 1.48 },
    { name: 'Breakout Expansion', signal: 'BUY', conf: 84, ret: '6.5%', dd: '2.5%', period: '7D', sharpe: 1.60 },
    { name: 'Pullback Retracement', signal: 'BUY', conf: 79, ret: '3.8%', dd: '1.6%', period: '4D', sharpe: 1.52 },
    { name: 'Pairs Trading Cointegration', signal: 'BUY', conf: 81, ret: '3.2%', dd: '1.2%', period: '5D', sharpe: 1.75 },
    { name: 'Statistical Arbitrage', signal: 'BUY', conf: 83, ret: '3.6%', dd: '1.4%', period: '4D', sharpe: 1.80 },
    { name: 'Sector Relative Strength', signal: 'BUY', conf: 77, ret: '4.0%', dd: '1.8%', period: '15D', sharpe: 1.45 },
    { name: 'Value / Quality FCF', signal: 'BUY', conf: 74, ret: '6.0%', dd: '2.5%', period: '30D', sharpe: 1.35 },
    { name: 'Growth Investing', signal: 'BUY', conf: 81, ret: '7.5%', dd: '3.0%', period: '20D', sharpe: 1.58 },
    { name: 'Event-Driven Catalyst', signal: 'BUY', conf: 75, ret: '5.0%', dd: '2.2%', period: '5D', sharpe: 1.50 },
    { name: 'Real-Time News Velocity', signal: 'BUY', conf: 78, ret: '3.5%', dd: '1.5%', period: '2D', sharpe: 1.42 },
    { name: 'Volatility Harvesting', signal: 'BUY', conf: 80, ret: '4.0%', dd: '1.8%', period: '7D', sharpe: 1.62 },
    { name: 'Machine Learning (LightGBM)', signal: 'BUY', conf: 85, ret: '4.6%', dd: '1.9%', period: '5D', sharpe: 1.85 },
    { name: 'Reinforcement Learning (PPO)', signal: 'BUY', conf: 82, ret: '4.4%', dd: '1.8%', period: '5D', sharpe: 1.78 },
  ];

  const positions = [
    { symbol: 'AAPL', shares: 80, entry: 228.40, current: 235.90, value: 18872.00, pnl: 600.00, pnlPct: 3.28, weight: 18.0 },
    { symbol: 'NVDA', shares: 120, entry: 121.50, current: 128.80, value: 15456.00, pnl: 876.00, pnlPct: 6.01, weight: 14.7 },
    { symbol: 'MSFT', shares: 35, entry: 440.10, current: 445.20, value: 15582.00, pnl: 178.50, pnlPct: 1.16, weight: 14.8 },
    { symbol: 'SPY', shares: 45, entry: 552.00, current: 558.20, value: 25119.00, pnl: 279.00, pnlPct: 1.12, weight: 24.0 },
  ];

  const handleSimulateCycle = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
      setNav(prev => prev + 340.50);
      setDailyPnl(prev => prev + 340.50);
    }, 1200);
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#070a13] text-slate-100 font-sans">
      {/* Institutional Top Navbar */}
      <header className="sticky top-0 z-50 border-b border-[#1c2740] bg-[#070a13]/95 backdrop-blur-md px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
              A
            </div>
            <div>
              <span className="font-bold text-lg tracking-wider text-white">ATHENA</span>
              <span className="text-[10px] text-cyan-400 block font-mono -mt-1 font-semibold">AI HEDGE FUND OS</span>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-2 pl-6 border-l border-[#1c2740] text-xs font-mono">
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> PAPER MODE
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
              <Lock className="w-3 h-3" /> LIVE TRADING: DISABLED
            </span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              REGIME: {regime} ({regimeConf}%)
            </span>
          </div>
        </div>

        {/* Action controls */}
        <div className="flex items-center space-x-4">
          <button
            onClick={handleSimulateCycle}
            disabled={isSimulating || killSwitchActive}
            className="px-3 py-1.5 rounded-md bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono text-xs font-medium flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
            {isSimulating ? 'EVALUATING PIPELINE...' : 'EXECUTE AI CYCLE'}
          </button>

          <button
            onClick={() => setKillSwitchActive(!killSwitchActive)}
            className={`px-3 py-1.5 rounded-md font-mono text-xs font-semibold flex items-center gap-1.5 transition-all ${
              killSwitchActive
                ? 'bg-rose-600 hover:bg-rose-500 text-white animate-pulse'
                : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/40'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            {killSwitchActive ? 'KILL SWITCH ACTIVE' : 'EMERGENCY KILL SWITCH'}
          </button>
        </div>
      </header>

      {/* Navigation Sub-header */}
      <div className="border-b border-[#1c2740] bg-[#0d1322] px-6 py-2 flex items-center justify-between overflow-x-auto text-xs font-mono">
        <div className="flex items-center space-x-1">
          {[
            { id: 'overview', label: 'EXECUTIVE OVERVIEW', icon: Activity },
            { id: 'markets', label: 'MARKETS & CHARTS', icon: BarChart3 },
            { id: 'agents', label: '14 AI AGENTS', icon: Bot },
            { id: 'strategies', label: '16 STRATEGIES', icon: Workflow },
            { id: 'debate', label: 'DEBATE & DECISION', icon: Scale },
            { id: 'risk', label: 'RISK VETO COCKPIT', icon: Shield },
            { id: 'portfolio', label: 'PORTFOLIO OPTIMIZER', icon: PieChart },
            { id: 'execution', label: 'PAPER TRADING', icon: Zap },
            { id: 'backtest', label: 'BACKTEST LAB', icon: Sliders },
            { id: 'journal', label: 'TRADE JOURNAL', icon: FileText },
            { id: 'learning', label: 'LEARNING & WEIGHTS', icon: Brain },
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-all ${
                  active
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Global Summary Stats */}
        <div className="hidden lg:flex items-center space-x-6 pl-4 font-mono text-xs">
          <div>
            <span className="text-slate-500 block text-[10px]">TOTAL NAV</span>
            <span className="font-bold text-slate-100">${nav.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">DAILY P&L</span>
            <span className="font-bold text-emerald-400 flex items-center gap-0.5">
              <ArrowUpRight className="w-3 h-3" /> +${dailyPnl.toFixed(2)} (+{dailyPnlPct}%)
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">SHARPE (60D)</span>
            <span className="font-bold text-cyan-400">1.85</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">1-DAY 95% VAR</span>
            <span className="font-bold text-amber-400">1.50%</span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* KILL SWITCH BANNER IF ACTIVE */}
        {killSwitchActive && (
          <div className="p-4 rounded-lg bg-rose-950/80 border border-rose-500/60 text-rose-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-6 h-6 text-rose-400 animate-bounce" />
              <div>
                <h4 className="font-bold text-sm font-mono">EMERGENCY KILL SWITCH ACTIVATED</h4>
                <p className="text-xs text-rose-300">All autonomous decision routing and broker order submissions are vetoed and blocked.</p>
              </div>
            </div>
            <button
              onClick={() => setKillSwitchActive(false)}
              className="px-3 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold"
            >
              DEACTIVATE KILL SWITCH
            </button>
          </div>
        )}

        {/* TAB 1: EXECUTIVE OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="terminal-card p-4">
                <span className="text-xs font-mono text-slate-400">PORTFOLIO NAV</span>
                <div className="text-2xl font-bold text-white mt-1 font-mono">${nav.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                <div className="text-xs font-mono text-emerald-400 mt-1 flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5" /> +$4,850.20 (+4.85% total)
                </div>
              </div>
              <div className="terminal-card p-4">
                <span className="text-xs font-mono text-slate-400">REALIZED DAILY P&L</span>
                <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">+${dailyPnl.toFixed(2)}</div>
                <div className="text-xs font-mono text-slate-400 mt-1">Win Rate: 64.2% (18/28 trades)</div>
              </div>
              <div className="terminal-card p-4">
                <span className="text-xs font-mono text-slate-400">ACTIVE REGIME ENSEMBLE</span>
                <div className="text-2xl font-bold text-cyan-400 mt-1 font-mono">{regime}</div>
                <div className="text-xs font-mono text-slate-400 mt-1">Ensemble Confidence: {regimeConf}%</div>
              </div>
              <div className="terminal-card p-4">
                <span className="text-xs font-mono text-slate-400">RISK METRICS (VAR/CVAR)</span>
                <div className="text-2xl font-bold text-amber-400 mt-1 font-mono">1.5% / 2.4%</div>
                <div className="text-xs font-mono text-emerald-400 mt-1">Gross Exposure: 71.5% NAV</div>
              </div>
            </div>

            {/* Middle Row: Equity Curve & Active Holdings */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="terminal-card lg:col-span-2 p-5 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-400" /> INTRADAY PORTFOLIO EQUITY CURVE (USD)
                  </h3>
                  <span className="text-xs font-mono text-emerald-400">+$1,450.30 Today</span>
                </div>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={equityData}>
                      <defs>
                        <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                      <YAxis domain={['dataMin - 500', 'dataMax + 500']} stroke="#64748b" tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#0d1322', borderColor: '#1c2740', fontSize: 12 }} />
                      <Area type="monotone" dataKey="nav" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#equityGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Active Positions Widget */}
              <div className="terminal-card p-5 flex flex-col">
                <h3 className="font-mono text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-cyan-400" /> ACTIVE HOLDINGS ({positions.length})
                </h3>
                <div className="space-y-3 flex-1 overflow-y-auto pr-1">
                  {positions.map(pos => (
                    <div key={pos.symbol} className="p-2.5 rounded bg-[#070a13]/80 border border-[#1c2740] flex items-center justify-between text-xs font-mono">
                      <div>
                        <div className="font-bold text-white flex items-center gap-1.5">
                          {pos.symbol} <span className="text-[10px] text-slate-400 font-normal">({pos.shares} sh)</span>
                        </div>
                        <div className="text-[11px] text-slate-400">Avg ${pos.entry.toFixed(2)} | Current ${pos.current.toFixed(2)}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-slate-200">${pos.value.toLocaleString()}</div>
                        <div className="text-emerald-400 text-[11px]">+{pos.pnlPct.toFixed(2)}% (+${pos.pnl.toFixed(0)})</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom Row: Recent Decisions & War Room Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="terminal-card p-5">
                <h3 className="font-mono text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Scale className="w-4 h-4 text-cyan-400" /> LATEST MULTI-AGENT TRADING DECISION
                </h3>
                <div className="p-4 rounded-lg bg-[#070a13] border border-cyan-500/30 font-mono text-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">ACTION: BUY AAPL</span>
                    <span className="text-cyan-400">Confidence: 82% (Platt Prob: 75%)</span>
                  </div>
                  <p className="text-slate-300 text-xs">
                    Multi-agent consensus achieved 93% agreement. Supported by Technical, Quant, Fundamental, Sentiment, and Macro agents.
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-[#1c2740]">
                    <div>Stop Loss: <span className="text-rose-400 font-bold">$246.66 (-5.7%)</span></div>
                    <div>Take Profit: <span className="text-emerald-400 font-bold">$290.10 (+10.9%)</span></div>
                    <div>Reward-to-Risk: <span className="text-cyan-400 font-bold">2.0:1</span></div>
                    <div>Risk Check: <span className="text-emerald-400 font-bold">APPROVED (Score 0.17)</span></div>
                  </div>
                </div>
              </div>

              <div className="terminal-card p-5">
                <h3 className="font-mono text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Bot className="w-4 h-4 text-cyan-400" /> 14 AGENT CONSENSUS RADAR
                </h3>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  {agentList.slice(0, 8).map(agent => (
                    <div key={agent.id} className="p-2 rounded bg-[#070a13] border border-[#1c2740] flex items-center justify-between">
                      <span className="text-slate-300 text-[11px] truncate max-w-[120px]">{agent.name}</span>
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                        agent.signal === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {agent.signal} {agent.conf}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: MARKETS & INTERACTIVE CANDLESTICK CHARTS */}
        {activeTab === 'markets' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center space-x-2 font-mono text-xs">
                <span className="text-slate-400">UNIVERSE:</span>
                {['AAPL', 'NVDA', 'MSFT', 'SPY', 'QQQ', 'BTC'].map(sym => (
                  <button
                    key={sym}
                    onClick={() => setSelectedSymbol(sym)}
                    className={`px-2.5 py-1 rounded font-bold transition-all ${
                      selectedSymbol === sym ? 'bg-cyan-600 text-white shadow-md shadow-cyan-500/30' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>

              <div className="font-mono text-xs flex items-center gap-4">
                <span className="text-slate-400">PRICE: <span className="text-white font-bold">$235.90</span></span>
                <span className="text-emerald-400 font-bold flex items-center"><ArrowUpRight className="w-3.5 h-3.5" /> +2.85% (Today)</span>
                <span className="text-slate-400">RSI(14): <span className="text-cyan-400 font-bold">58.4</span></span>
              </div>
            </div>

            {/* Interactive Candlestick / Area Chart */}
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200">
                  {selectedSymbol} / USD - DAILY OHLCV WITH EMA 50 & EMA 200 OVERLAYS
                </h3>
                <span className="text-xs font-mono text-cyan-400">Volume-Weighted Momentum</span>
              </div>

              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={candleData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis domain={['dataMin - 5', 'dataMax + 5']} stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0d1322', borderColor: '#1c2740', fontSize: 12 }} />
                    <Line type="monotone" dataKey="close" stroke="#06b6d4" strokeWidth={2.5} name="Close Price" dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="ema50" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 4" name="EMA 50" dot={false} />
                    <Line type="monotone" dataKey="ema200" stroke="#818cf8" strokeWidth={1.5} strokeDasharray="2 2" name="EMA 200" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Microstructure Order Book & Quantitative Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="terminal-card p-5">
                <h3 className="font-mono text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" /> L2 ORDER BOOK DEPTH SNAPSHOT
                </h3>
                <div className="grid grid-cols-2 gap-4 font-mono text-xs">
                  <div className="space-y-1">
                    <span className="text-emerald-400 font-bold block mb-1">BIDS (BUY QUEUE)</span>
                    {[
                      { price: 235.85, size: 450 },
                      { price: 235.80, size: 820 },
                      { price: 235.75, size: 1200 },
                      { price: 235.70, size: 650 },
                      { price: 235.65, size: 900 },
                    ].map((b, i) => (
                      <div key={i} className="flex justify-between px-2 py-1 rounded bg-emerald-950/20 text-emerald-300">
                        <span>${b.price.toFixed(2)}</span>
                        <span>{b.size} sh</span>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-1">
                    <span className="text-rose-400 font-bold block mb-1">ASKS (SELL QUEUE)</span>
                    {[
                      { price: 235.95, size: 380 },
                      { price: 236.00, size: 710 },
                      { price: 236.05, size: 1100 },
                      { price: 236.10, size: 540 },
                      { price: 236.15, size: 880 },
                    ].map((a, i) => (
                      <div key={i} className="flex justify-between px-2 py-1 rounded bg-rose-950/20 text-rose-300">
                        <span>${a.price.toFixed(2)}</span>
                        <span>{a.size} sh</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="terminal-card p-5">
                <h3 className="font-mono text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" /> EXTRACTED QUANTITATIVE FEATURES
                </h3>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs text-slate-300">
                  <div className="p-2 rounded bg-[#070a13] border border-[#1c2740]">
                    <span className="text-slate-500 text-[10px] block">RSI (14-DAY)</span>
                    <span className="font-bold text-white">58.4 (Neutral Bull)</span>
                  </div>
                  <div className="p-2 rounded bg-[#070a13] border border-[#1c2740]">
                    <span className="text-slate-500 text-[10px] block">MACD HISTOGRAM</span>
                    <span className="font-bold text-emerald-400">+0.485 (Expanding)</span>
                  </div>
                  <div className="p-2 rounded bg-[#070a13] border border-[#1c2740]">
                    <span className="text-slate-500 text-[10px] block">REALIZED VOLATILITY</span>
                    <span className="font-bold text-white">22.4% Annualized</span>
                  </div>
                  <div className="p-2 rounded bg-[#070a13] border border-[#1c2740]">
                    <span className="text-slate-500 text-[10px] block">BID/ASK SPREAD</span>
                    <span className="font-bold text-cyan-400">3.5 bps</span>
                  </div>
                  <div className="p-2 rounded bg-[#070a13] border border-[#1c2740]">
                    <span className="text-slate-500 text-[10px] block">GAMMA EXPOSURE (GEX)</span>
                    <span className="font-bold text-emerald-400">+$2.5M Positive Pin</span>
                  </div>
                  <div className="p-2 rounded bg-[#070a13] border border-[#1c2740]">
                    <span className="text-slate-500 text-[10px] block">CROSS-ASSET RISK-ON</span>
                    <span className="font-bold text-emerald-400">0.72 / 1.0</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: 14 AI AGENTS WAR ROOM */}
        {activeTab === 'agents' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="font-mono text-sm font-semibold text-slate-200">
                ATHENA MULTI-AGENT WAR ROOM - 14 AUTONOMOUS INTELLIGENCE AGENTS
              </h3>
              <span className="text-xs font-mono text-emerald-400">All Agents Healthy (100% Uptime)</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentList.map(agent => (
                <div key={agent.id} className="terminal-card p-4 flex flex-col justify-between hover:border-cyan-500/50 transition-all">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                        <Bot className="w-3.5 h-3.5 text-cyan-400" /> {agent.name}
                      </span>
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                        agent.signal === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : (agent.signal === 'PASS' ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-700 text-slate-300')
                      }`}>
                        {agent.signal} ({agent.conf}%)
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-mono mb-3 leading-relaxed">
                      {agent.reason}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-[#1c2740] grid grid-cols-3 text-[10px] font-mono text-slate-400">
                    <div>Exp Ret: <span className="text-emerald-400 font-bold">{agent.ret}</span></div>
                    <div>Risk: <span className="text-rose-400 font-bold">{agent.risk}</span></div>
                    <div className="text-right">Latency: <span className="text-cyan-400 font-bold">{agent.latency}ms</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: 16 QUANTITATIVE STRATEGIES */}
        {activeTab === 'strategies' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="font-mono text-sm font-semibold text-slate-200">
                16 INDEPENDENT QUANTITATIVE TRADING STRATEGIES
              </h3>
              <span className="text-xs font-mono text-cyan-400">Regime Weighting Active</span>
            </div>

            <div className="terminal-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-[#070a13] text-slate-400 border-b border-[#1c2740]">
                    <tr>
                      <th className="p-3">STRATEGY NAME</th>
                      <th className="p-3">SIGNAL</th>
                      <th className="p-3">CONFIDENCE</th>
                      <th className="p-3">EXP RETURN</th>
                      <th className="p-3">MAX DRAWDOWN</th>
                      <th className="p-3">HOLDING PERIOD</th>
                      <th className="p-3">HISTORICAL SHARPE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1c2740]">
                    {strategyList.map(strat => (
                      <tr key={strat.name} className="hover:bg-slate-800/30 transition-colors">
                        <td className="p-3 font-bold text-white flex items-center gap-2">
                          <Workflow className="w-3.5 h-3.5 text-cyan-400" /> {strat.name}
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            strat.signal === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'
                          }`}>
                            {strat.signal}
                          </span>
                        </td>
                        <td className="p-3 text-cyan-300 font-bold">{strat.conf}%</td>
                        <td className="p-3 text-emerald-400 font-bold">+{strat.ret}</td>
                        <td className="p-3 text-rose-400">-{strat.dd}</td>
                        <td className="p-3 text-slate-300">{strat.period}</td>
                        <td className="p-3 text-amber-400 font-bold">{strat.sharpe.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: DIALECTICAL DEBATE & DECISION */}
        {activeTab === 'debate' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Scale className="w-4 h-4 text-cyan-400" /> DIALECTICAL MULTI-AGENT DEBATE SYNTHESIS
                </h3>
                <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono text-xs">
                  Consensus Agreement Score: 93%
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/30 space-y-2 font-mono text-xs">
                  <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                    <ArrowUpRight className="w-4 h-4" /> BULLISH ARGUMENTS & EVIDENCE (13 AGENTS)
                  </span>
                  <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                    <li><strong>[TECHNICAL]</strong> EMA 9 &gt; 21 golden cross above 50-day moving average.</li>
                    <li><strong>[QUANT]</strong> 60-day Sharpe of 1.85 with +4.5% annual residual alpha.</li>
                    <li><strong>[FUNDAMENTAL]</strong> ROE at 28.0% with strong enterprise cash flow growth.</li>
                    <li><strong>[OPTIONS]</strong> Positive dealer gamma pin providing volatility dampening.</li>
                  </ul>
                </div>

                <div className="p-4 rounded-lg bg-rose-950/20 border border-rose-500/30 space-y-2 font-mono text-xs">
                  <span className="text-rose-400 font-bold flex items-center gap-1.5">
                    <ArrowDownRight className="w-4 h-4" /> COUNTER-THESIS & CONFLICTS (1 AGENT)
                  </span>
                  <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                    <li><strong>[VALUATION CONFLICT]</strong> P/E multiple (24.5x) requires continuous execution.</li>
                    <li><strong>[MACRO HAZARD]</strong> Upcoming central bank rate commentary may induce short-term chop.</li>
                  </ul>
                </div>
              </div>

              <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] font-mono text-xs space-y-2">
                <span className="text-cyan-400 font-bold block">DIALECTICAL SYNTHESIS CONCLUSION</span>
                <p className="text-slate-200 leading-relaxed">
                  The consensus among 13 out of 14 agents strongly warrants a BUY position on AAPL. The single point of valuation friction is mitigated by tight ATR trailing stop-losses. Statistical evidence validation confirms positive expected return (+4.8%) net of all slippage and spread friction.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: RISK COCKPIT */}
        {activeTab === 'risk' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-cyan-400" /> INDEPENDENT RISK MANAGEMENT VETO COCKPIT
                </h3>
                <span className="text-xs font-mono text-emerald-400 font-bold">ALL RISK BOUNDS NOMINAL</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">MAX DAILY LOSS LIMIT</span>
                  <span className="text-lg font-bold text-white">$5,000.00</span>
                  <div className="text-emerald-400 text-[10px] mt-1">Current Loss: $0.00 (In Profit)</div>
                </div>
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">MAX SINGLE POSITION CAP</span>
                  <span className="text-lg font-bold text-white">$50,000.00 (50% NAV)</span>
                  <div className="text-cyan-400 text-[10px] mt-1">Current Max: $25,119.00 (SPY)</div>
                </div>
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">MAX ALLOWED DRAWDOWN</span>
                  <span className="text-lg font-bold text-white">15.0% Kill Threshold</span>
                  <div className="text-emerald-400 text-[10px] mt-1">Current Drawdown: 0.0%</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: PORTFOLIO OPTIMIZER */}
        {activeTab === 'portfolio' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-cyan-400" /> CONVEX PORTFOLIO OPTIMIZER & REBALANCING
                </h3>
                <div className="flex items-center space-x-2 font-mono text-xs">
                  {['MAX_SHARPE', 'RISK_PARITY', 'KELLY_CRITERION', 'MIN_CVAR'].map(obj => (
                    <button
                      key={obj}
                      onClick={() => setOptimizerObjective(obj)}
                      className={`px-2.5 py-1 rounded font-bold ${
                        optimizerObjective === obj ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                    >
                      {obj.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
                <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] space-y-3">
                  <span className="text-cyan-400 font-bold block">TARGET ALLOCATION WEIGHTS</span>
                  <div className="space-y-2">
                    {[
                      { sym: 'AAPL', target: 20.0, current: 18.0, delta: '+2.0%' },
                      { sym: 'NVDA', target: 22.0, current: 14.7, delta: '+7.3%' },
                      { sym: 'MSFT', target: 18.0, current: 14.8, delta: '+3.2%' },
                      { sym: 'SPY', target: 30.0, current: 24.0, delta: '+6.0%' },
                      { sym: 'CASH', target: 10.0, current: 28.5, delta: '-18.5%' },
                    ].map(item => (
                      <div key={item.sym} className="flex justify-between items-center p-2 rounded bg-[#0d1322] border border-[#1c2740]">
                        <span className="font-bold text-white">{item.sym}</span>
                        <div className="flex items-center gap-4">
                          <span className="text-slate-400">Target: {item.target}%</span>
                          <span className="text-slate-300">Actual: {item.current}%</span>
                          <span className="text-emerald-400 font-bold">{item.delta}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] space-y-3">
                  <span className="text-cyan-400 font-bold block">OPTIMIZED PORTFOLIO METRICS</span>
                  <div className="space-y-2">
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span className="text-slate-400">Expected Annual Return</span>
                      <span className="font-bold text-emerald-400">+19.4%</span>
                    </div>
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span className="text-slate-400">Expected Annual Volatility</span>
                      <span className="font-bold text-amber-400">12.8%</span>
                    </div>
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span className="text-slate-400">Portfolio Sharpe Ratio</span>
                      <span className="font-bold text-cyan-400">1.52</span>
                    </div>
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span className="text-slate-400">1-Day 95% CVaR</span>
                      <span className="font-bold text-rose-400">2.15%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 8: PAPER EXECUTION */}
        {activeTab === 'execution' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-cyan-400" /> DETERMINISTIC PAPER TRADING CONSOLE
                </h3>
                <span className="text-xs font-mono text-emerald-400">Paper Broker Active (Latency: 50ms)</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
                <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] space-y-3">
                  <span className="text-cyan-400 font-bold block">MANUAL PAPER ORDER TICKET</span>
                  <div className="space-y-2">
                    <div>
                      <label className="text-slate-400 text-[10px] block mb-1">SYMBOL</label>
                      <input type="text" defaultValue="AAPL" className="w-full p-2 rounded bg-[#0d1322] border border-[#1c2740] text-white" />
                    </div>
                    <div>
                      <label className="text-slate-400 text-[10px] block mb-1">QUANTITY</label>
                      <input type="number" defaultValue="25" className="w-full p-2 rounded bg-[#0d1322] border border-[#1c2740] text-white" />
                    </div>
                    <div className="grid grid-cols-2 gap-2 pt-2">
                      <button className="p-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold">PAPER BUY</button>
                      <button className="p-2 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold">PAPER SELL</button>
                    </div>
                  </div>
                </div>

                <div className="md:col-span-2 p-4 rounded bg-[#070a13] border border-[#1c2740] space-y-2">
                  <span className="text-cyan-400 font-bold block">RECENT SIMULATED EXECUTION FILLS</span>
                  <div className="space-y-1.5 overflow-y-auto max-h-48">
                    {[
                      { id: 'fill-01', time: '15:28:10', side: 'BUY', sym: 'AAPL', qty: 19, px: 261.60, slip: '8.2 bps', fee: '$0.10' },
                      { id: 'fill-02', time: '14:15:02', side: 'BUY', sym: 'NVDA', qty: 30, px: 128.85, slip: '4.5 bps', fee: '$0.15' },
                      { id: 'fill-03', time: '11:40:22', side: 'BUY', sym: 'MSFT', qty: 10, px: 445.30, slip: '3.1 bps', fee: '$0.05' },
                    ].map(f => (
                      <div key={f.id} className="p-2 rounded bg-[#0d1322] border border-[#1c2740] flex justify-between items-center text-[11px]">
                        <span className="text-slate-400">{f.time}</span>
                        <span className="text-emerald-400 font-bold">{f.side} {f.qty} {f.sym}</span>
                        <span className="text-white">${f.px.toFixed(2)}</span>
                        <span className="text-slate-400">Slip: {f.slip}</span>
                        <span className="text-cyan-400">Fee: {f.fee}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 9: BACKTEST LAB */}
        {activeTab === 'backtest' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-400" /> EVENT-DRIVEN BACKTEST LAB & MONTE CARLO (1,000 PATHS)
                </h3>
                <span className="text-xs font-mono text-emerald-400 font-bold">Zero Look-Ahead Bias Mode</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs mb-6">
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">TOTAL RETURN</span>
                  <span className="text-lg font-bold text-emerald-400">+32.50%</span>
                </div>
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">CAGR</span>
                  <span className="text-lg font-bold text-cyan-400">32.50%</span>
                </div>
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">SHARPE RATIO</span>
                  <span className="text-lg font-bold text-amber-400">1.85</span>
                </div>
                <div className="p-3 rounded bg-[#070a13] border border-[#1c2740]">
                  <span className="text-slate-500 block">MAX DRAWDOWN</span>
                  <span className="text-lg font-bold text-rose-400">8.90%</span>
                </div>
              </div>

              <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] font-mono text-xs space-y-2">
                <span className="text-cyan-400 font-bold block">MONTE CARLO PROBABILITY ANALYSIS</span>
                <p className="text-slate-300">
                  Median Expected CAGR: <strong>+31.0%</strong> | 95th Percentile Max Drawdown: <strong>16.5%</strong> | Probability of Ruin: <strong>&lt; 0.01%</strong>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 10: TRADE JOURNAL & EXPLAINABILITY */}
        {activeTab === 'journal' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-cyan-400" /> HISTORICAL TRADE JOURNAL & EXPLAINABILITY REPORTS
                </h3>
                <span className="text-xs font-mono text-slate-400">Semantic Search Active</span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {[
                  { id: 'TRD-AAPL-DF1C4B', sym: 'AAPL', side: 'BUY', time: '2026-08-29 11:51', px: 261.60, pnl: '+4.8%', conf: '82%', status: 'FILLED' },
                  { id: 'TRD-NVDA-9A2E1C', sym: 'NVDA', side: 'BUY', time: '2026-08-28 14:15', px: 121.50, pnl: '+6.0%', conf: '86%', status: 'CLOSED' },
                  { id: 'TRD-MSFT-7B1F3D', sym: 'MSFT', side: 'BUY', time: '2026-08-27 10:30', px: 440.10, pnl: '+1.2%', conf: '79%', status: 'OPEN' },
                ].map(trade => (
                  <div key={trade.id} className="p-3 rounded bg-[#070a13] border border-[#1c2740] flex items-center justify-between hover:border-cyan-500/50 transition-all">
                    <div>
                      <div className="font-bold text-white flex items-center gap-2">
                        <span>{trade.id}</span>
                        <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 text-[10px]">{trade.side} {trade.sym}</span>
                        <span className="text-slate-400 text-[10px]">{trade.time}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">Fill Price: ${trade.px.toFixed(2)} | Confidence: {trade.conf}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-emerald-400">{trade.pnl}</span>
                      <button
                        onClick={() => setSelectedTrade(trade)}
                        className="px-2.5 py-1 rounded bg-cyan-600/30 hover:bg-cyan-600 text-cyan-200 text-[11px]"
                      >
                        VIEW REPORT
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Explainability Report Viewer Modal */}
            {selectedTrade && (
              <div className="terminal-card p-6 border-cyan-500/50 font-mono text-xs space-y-4">
                <div className="flex items-center justify-between border-b border-[#1c2740] pb-3">
                  <h4 className="font-bold text-cyan-300 text-sm">TRADE EXPLAINABILITY REPORT - {selectedTrade.id}</h4>
                  <button onClick={() => setSelectedTrade(null)} className="text-slate-400 hover:text-white font-bold">CLOSE [X]</button>
                </div>
                <div className="space-y-2 text-slate-200">
                  <p><strong>Decision:</strong> BUY {selectedTrade.sym} at ${selectedTrade.px.toFixed(2)}</p>
                  <p><strong>Supporting Agents:</strong> Technical, Quant, Fundamental, Sentiment, Macro, Microstructure, Options, Cross-Asset</p>
                  <p><strong>Why Approved:</strong> Cleared multi-agent debate (93% consensus) and passed independent risk checks with 0.17 risk score.</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 11: LEARNING & BAYESIAN WEIGHTS */}
        {activeTab === 'learning' && (
          <div className="space-y-6">
            <div className="terminal-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-cyan-400" /> OFFLINE BAYESIAN LEARNING & PROBABILITY CALIBRATION
                </h3>
                <span className="text-xs font-mono text-amber-400">Human Operator Approval Gate Active</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
                <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] space-y-3">
                  <span className="text-cyan-400 font-bold block">BAYESIAN AGENT WEIGHT ATTRIBUTION</span>
                  <div className="space-y-2">
                    {[
                      { name: 'Quant Agent', prev: 0.25, updated: 0.28, delta: '+0.03' },
                      { name: 'Technical Agent', prev: 0.15, updated: 0.16, delta: '+0.01' },
                      { name: 'Fundamental Agent', prev: 0.20, updated: 0.21, delta: '+0.01' },
                      { name: 'Microstructure Agent', prev: 0.15, updated: 0.14, delta: '-0.01' },
                      { name: 'Macro Agent', prev: 0.15, updated: 0.13, delta: '-0.02' },
                      { name: 'Sentiment Agent', prev: 0.10, updated: 0.08, delta: '-0.02' },
                    ].map(w => (
                      <div key={w.name} className="flex justify-between items-center p-2 rounded bg-[#0d1322]">
                        <span className="text-white font-bold">{w.name}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400">{w.prev.toFixed(2)} -&gt; {w.updated.toFixed(2)}</span>
                          <span className={w.delta.startsWith('+') ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>{w.delta}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded bg-[#070a13] border border-[#1c2740] space-y-3">
                  <span className="text-cyan-400 font-bold block">PLATT SCALING PROBABILITY CALIBRATION</span>
                  <div className="space-y-2 text-slate-300">
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span>Brier Score (Lower is better)</span>
                      <span className="text-emerald-400 font-bold">0.112</span>
                    </div>
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span>Expected Calibration Error (ECE)</span>
                      <span className="text-emerald-400 font-bold">3.4%</span>
                    </div>
                    <div className="p-2 rounded bg-[#0d1322] flex justify-between">
                      <span>Maximum Calibration Error (MCE)</span>
                      <span className="text-cyan-400 font-bold">7.0%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
