"""
GeminiQuant / OmniQuant Vercel Serverless Gateway & Interactive Web Dashboard
"""
from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Add project root to sys.path for serverless imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.models.types import AssetClass, OrderSide, OrderType  # noqa: E402
from core.models.order import OrderRequest  # noqa: E402
from core.models.market_data import TickData  # noqa: E402
from research.graph import research_graph  # noqa: E402
from research.memory import research_memory  # noqa: E402
from decision.state_builder import state_builder  # noqa: E402
from decision.laya_engine import laya_engine  # noqa: E402
from execution.oms import oms  # noqa: E402
from risk.risk_manager import risk_manager  # noqa: E402

app = FastAPI(
    title="GeminiQuant Platform",
    description="Multi-Asset Intelligent Quantitative Trading System",
    version="0.1.0"
)

class EvaluateRequest(BaseModel):
    symbol: str = "BTC/USDT"
    asset_class: str = "CRYPTO"
    price: float = 85980.0
    rsi: float = 28.5
    regime: str = "BULL_EXPANSION"
    drawdown: float = 0.5

class SimulateOrderRequest(BaseModel):
    symbol: str = "600519.SH"
    asset_class: str = "EQUITY_CN"
    side: str = "SELL"
    price: float = 51.20
    volume: float = 100.0
    test_scenario: Optional[str] = "t_plus_1" # 'normal', 't_plus_1', 'limit_up', 'drawdown'

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeminiQuant - 全资产智能量化交易平台</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #e2e8f0; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glass-card:hover { border-color: rgba(59, 130, 246, 0.4); transform: translateY(-2px); transition: all 0.2s ease; }
        .tab-btn.active { background-color: #2563eb; color: white; border-color: #3b82f6; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        <!-- Header -->
        <header class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 glass p-6 rounded-2xl">
            <div>
                <div class="flex items-center gap-3">
                    <div class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></div>
                    <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                        <span>GeminiQuant</span>
                        <span class="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">v0.1.0 生产环境</span>
                    </h1>
                </div>
                <p class="text-slate-400 text-sm mt-1">覆盖 A股 · 港美股 · Crypto · 黄金白银 · 商品期货 · 期权 全资产多智能体系统</p>
            </div>
            <div class="flex flex-wrap items-center gap-3">
                <a href="/docs" target="_blank" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">Swagger API 接口文档</a>
                <a href="https://github.com/CrazyRock114/geminiquant" target="_blank" class="px-4 py-2 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition flex items-center gap-2">
                    <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    GitHub 仓库
                </a>
            </div>
        </header>

        <!-- KPI Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">账户总动态权益 (Equity)</div>
                <div class="text-2xl font-bold text-white mono mt-1" id="kpi-equity">¥ 1,009,874.68</div>
                <div class="text-xs text-emerald-400 mt-2 flex items-center gap-1 font-semibold">
                    <span>▲ +0.99%</span>
                    <span class="text-slate-500 font-normal">日内动态收益</span>
                </div>
            </div>
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">System 1 (Laya 决策时延)</div>
                <div class="text-2xl font-bold text-blue-400 mono mt-1" id="kpi-latency">&lt; 0.02 ms</div>
                <div class="text-xs text-slate-400 mt-2">非自回归判别模型 · 零幻觉</div>
            </div>
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">System 2 (TradingAgents 宏观)</div>
                <div class="text-2xl font-bold text-emerald-400 mt-1" id="kpi-regime">BULL EXPANSION</div>
                <div class="text-xs text-slate-400 mt-2">多空博弈共识: 多头占优 (72%)</div>
            </div>
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">System 0 (风控与撮合底座)</div>
                <div class="text-2xl font-bold text-purple-400 mt-1">QIFI Active</div>
                <div class="text-xs text-slate-400 mt-2">CTP / QMT / CCXT / IBKR</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="flex flex-wrap items-center gap-2 p-1.5 glass rounded-2xl border border-slate-800">
            <button onclick="switchTab('tab-markets')" id="btn-markets" class="tab-btn active px-4 py-2 text-xs font-semibold rounded-xl transition border border-transparent">
                📊 六大市场监控看板
            </button>
            <button onclick="switchTab('tab-laya')" id="btn-laya" class="tab-btn px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white transition border border-transparent">
                ⚡️ Laya 毫秒决策模拟器
            </button>
            <button onclick="switchTab('tab-research')" id="btn-research" class="tab-btn px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white transition border border-transparent">
                🧠 TradingAgents 投研辩论室
            </button>
            <button onclick="switchTab('tab-risk')" id="btn-risk" class="tab-btn px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white transition border border-transparent">
                🛡 前置硬核风控与模拟报单
            </button>
        </div>

        <!-- TAB 1: Markets Watch -->
        <div id="tab-markets" class="tab-content space-y-4">
            <div class="glass p-6 rounded-2xl space-y-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="text-lg font-semibold text-white">六大标的实时行情与信号</h2>
                        <p class="text-xs text-slate-400">点击右侧“⚡️ 立即评估”可直接触发 Laya 实时判决</p>
                    </div>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="text-xs text-slate-400 border-b border-slate-800">
                            <tr>
                                <th class="pb-3">标的代码</th>
                                <th class="pb-3">资产分类</th>
                                <th class="pb-3">最新行情</th>
                                <th class="pb-3">当前信号</th>
                                <th class="pb-3">前置风控状态</th>
                                <th class="pb-3 text-right">实时操作</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800/60 mono text-xs">
                            <tr class="hover:bg-slate-800/30 transition">
                                <td class="py-3.5 font-bold text-white">BTC/USDT</td>
                                <td class="text-slate-400 font-sans">Crypto 永续</td>
                                <td class="text-emerald-400 font-semibold">$85,980.76</td>
                                <td><span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">REDUCE / PASSIVE</span></td>
                                <td class="text-emerald-400 font-sans">✓ 风控全项放行</td>
                                <td class="text-right">
                                    <button onclick="runQuickEval('BTC/USDT', 'CRYPTO', 85980.76, 28.5)" class="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-sans transition">⚡️ 立即评估</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-800/30 transition">
                                <td class="py-3.5 font-bold text-white">AU2412 (沪金)</td>
                                <td class="text-slate-400 font-sans">贵金属 / CTP 期货</td>
                                <td class="text-yellow-400 font-semibold">¥618.50</td>
                                <td><span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">REDUCE / PASSIVE</span></td>
                                <td class="text-emerald-400 font-sans">✓ 风控全项放行</td>
                                <td class="text-right">
                                    <button onclick="runQuickEval('AU2412', 'PRECIOUS_METALS', 618.50, 45.0)" class="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-sans transition">⚡️ 立即评估</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-800/30 transition">
                                <td class="py-3.5 font-bold text-white">RB2501 (螺纹钢)</td>
                                <td class="text-slate-400 font-sans">商品期货 / CTP</td>
                                <td class="text-slate-300 font-semibold">¥618.50</td>
                                <td><span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">REDUCE / PASSIVE</span></td>
                                <td class="text-emerald-400 font-sans">✓ 风控全项放行</td>
                                <td class="text-right">
                                    <button onclick="runQuickEval('RB2501', 'COMMODITY_FUTURES', 618.50, 52.0)" class="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-sans transition">⚡️ 立即评估</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-800/30 transition">
                                <td class="py-3.5 font-bold text-white">600519.SH (贵州茅台)</td>
                                <td class="text-slate-400 font-sans">A 股主板</td>
                                <td class="text-slate-300 font-semibold">¥51.20</td>
                                <td><span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">REDUCE</span></td>
                                <td class="text-amber-400 font-sans">⚠ A股 T+1 保护拦截</td>
                                <td class="text-right">
                                    <button onclick="runQuickEval('600519.SH', 'EQUITY_CN', 51.20, 68.0)" class="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-sans transition">⚡️ 立即评估</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-800/30 transition">
                                <td class="py-3.5 font-bold text-white">AAPL.US (苹果)</td>
                                <td class="text-slate-400 font-sans">美股 (IBKR 网关)</td>
                                <td class="text-slate-300 font-semibold">$51.20</td>
                                <td><span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">REDUCE</span></td>
                                <td class="text-emerald-400 font-sans">✓ 风控全项放行</td>
                                <td class="text-right">
                                    <button onclick="runQuickEval('AAPL.US', 'EQUITY_US_HK', 51.20, 58.0)" class="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-sans transition">⚡️ 立即评估</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-800/30 transition">
                                <td class="py-3.5 font-bold text-white">10005101 (50ETF期权)</td>
                                <td class="text-slate-400 font-sans">股票期权 / Greeks</td>
                                <td class="text-purple-400 font-semibold">¥2.60</td>
                                <td><span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">REDUCE</span></td>
                                <td class="text-rose-400 font-sans">✕ 裸卖空防穿仓拦截</td>
                                <td class="text-right">
                                    <button onclick="runQuickEval('10005101', 'OPTIONS', 2.60, 72.0)" class="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-sans transition">⚡️ 立即评估</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: Laya Simulator -->
        <div id="tab-laya" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Control Panel -->
                <div class="glass p-6 rounded-2xl space-y-5">
                    <h2 class="text-lg font-semibold text-white flex items-center gap-2">
                        <span>🎛</span> Laya 决策输入特征调参台
                    </h2>
                    <div class="space-y-4 text-xs">
                        <div>
                            <label class="text-slate-400 flex justify-between">
                                <span>RSI 相对强弱指标:</span>
                                <span id="val-rsi" class="text-blue-400 font-bold mono">28.5</span>
                            </label>
                            <input type="range" id="input-rsi" min="10" max="90" value="28" step="1" oninput="updateLayaFromSliders()" class="w-full mt-1.5 accent-blue-500">
                        </div>
                        <div>
                            <label class="text-slate-400 flex justify-between">
                                <span>账户单日动态回撤 (%):</span>
                                <span id="val-dd" class="text-amber-400 font-bold mono">0.5%</span>
                            </label>
                            <input type="range" id="input-dd" min="0" max="5" value="0.5" step="0.1" oninput="updateLayaFromSliders()" class="w-full mt-1.5 accent-amber-500">
                            <div class="text-[10px] text-slate-500 mt-0.5">注：超过 3.0% 将直接触发日内熔断锁死</div>
                        </div>
                        <div>
                            <label class="text-slate-400">System 2 宏观研报环境 (Macro Regime):</label>
                            <select id="input-regime" onchange="updateLayaFromSliders()" class="w-full mt-1.5 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white">
                                <option value="BULL_EXPANSION">BULL_EXPANSION (强多头扩张期)</option>
                                <option value="RANGE_BOUND">RANGE_BOUND (宽幅震荡洗盘期)</option>
                                <option value="BEAR_CONTRACTION">BEAR_CONTRACTION (弱空头收缩期)</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-slate-400">测试标的:</label>
                            <select id="input-symbol" onchange="updateLayaFromSliders()" class="w-full mt-1.5 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white">
                                <option value="BTC/USDT">BTC/USDT (Crypto)</option>
                                <option value="AU2412">AU2412 (沪金)</option>
                                <option value="600519.SH">600519.SH (A股)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Output Panel -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-lg font-semibold text-white flex items-center justify-between">
                        <span>⚡️ Laya 极速推理结果</span>
                        <span id="laya-latency-badge" class="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 mono">耗时: 0.01 ms</span>
                    </h2>
                    <div class="space-y-3 mono text-xs">
                        <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                            <div class="flex justify-between">
                                <span class="text-slate-400">Action (动作选择):</span>
                                <span id="res-action" class="text-lg font-bold text-emerald-400">STRONG_BUY</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Urgency (紧迫度):</span>
                                <span id="res-urgency" class="text-blue-300">AGGRESSIVE_TAKER</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Confidence (置信度):</span>
                                <span id="res-confidence" class="text-purple-300">HIGH (92.0%)</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Risk Check Passed:</span>
                                <span id="res-risk" class="text-emerald-400">TRUE (放行)</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Size Factor (调仓比例):</span>
                                <span id="res-size" class="text-slate-200">FULL (100%)</span>
                            </div>
                        </div>
                        <div class="p-3 rounded-xl bg-slate-800/40 text-[11px] text-slate-400 font-sans">
                            💡 <span class="font-semibold text-slate-300">非自回归判别优势：</span> 直接输出确定性概率标签，彻底消除传统生成式 LLM 逐字生成的数秒延迟与交易幻觉。
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 3: TradingAgents Research -->
        <div id="tab-research" class="tab-content hidden space-y-6">
            <div class="glass p-6 rounded-2xl space-y-5">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                        <h2 class="text-lg font-semibold text-white">TradingAgents 投研委员会分析</h2>
                        <p class="text-xs text-slate-400">模拟买方投资机构：基本面分析师、舆情分析师、技术分析师与多空激烈辩论</p>
                    </div>
                    <button onclick="triggerResearchDebate()" id="btn-run-debate" class="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 transition flex items-center gap-2">
                        <span>▶ 立即启动投研辩论</span>
                    </button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
                        <div class="text-blue-400 font-bold">1. 基本面分析师 (Fundamental)</div>
                        <p id="deb-fund" class="text-slate-300 leading-relaxed">AU2412 具备强劲央行购金与实际利率下行支撑，估值分位数处于合理安全边际区间。</p>
                        <div class="text-slate-500 text-[10px]">评分: 0.75 / 1.0</div>
                    </div>
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
                        <div class="text-purple-400 font-bold">2. 舆情与新闻分析师 (Sentiment)</div>
                        <p id="deb-sent" class="text-slate-300 leading-relaxed">社交媒体与主流财经常态讨论以地缘避险与宽松政策为主，情绪维持健康温和乐观。</p>
                        <div class="text-slate-500 text-[10px]">评分: 0.68 / 1.0</div>
                    </div>
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
                        <div class="text-yellow-400 font-bold">3. 技术面分析师 (Technical)</div>
                        <p id="deb-tech" class="text-slate-300 leading-relaxed">日线级别均线呈现多头排列，突破 20 日盘整箱体平台，成交量温和有效放大。</p>
                        <div class="text-slate-500 text-[10px]">评分: 0.70 / 1.0</div>
                    </div>
                </div>

                <!-- Debate Outcome Card -->
                <div class="p-5 rounded-xl bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30 space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-blue-400 uppercase tracking-wider">多空质询辩论决议 (Bull vs Bear Consensus)</span>
                        <span id="deb-winner-badge" class="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold">BULL WINNER (多头胜出)</span>
                    </div>
                    <div class="text-sm text-white font-medium" id="deb-catalyst">
                        核心催化剂：多周期均线突破共振与海外流动性改善
                    </div>
                    <div class="text-xs text-slate-400">
                        该决议已自动同步持久化至 System 2 缓存中，供下游 Laya 毫秒级决策引擎作为静态宏观槽调用。
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 4: Risk & Order Simulation -->
        <div id="tab-risk" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Trigger Risk Scenarios -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-lg font-semibold text-white">触发前置风控拦截场景验证</h2>
                    <p class="text-xs text-slate-400">选择不同违规报单指令，亲身体验毫秒级风控熔断机制：</p>
                    
                    <div class="space-y-2.5">
                        <button onclick="testOrderScenario('t_plus_1')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-amber-500/50 transition">
                            <div class="text-xs font-bold text-amber-400">测试 1: A 股 T+1 卖出违规拦截</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟卖出今日刚刚买入的 100 股贵州茅台 (可用持仓 = 0)</div>
                        </button>
                        <button onclick="testOrderScenario('limit_up')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-rose-500/50 transition">
                            <div class="text-xs font-bold text-rose-400">测试 2: 涨停板追高买入拦截</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟以涨停价 ¥1760 追买已封涨停的股票</div>
                        </button>
                        <button onclick="testOrderScenario('drawdown')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-rose-500/50 transition">
                            <div class="text-xs font-bold text-rose-400">测试 3: 账户单日回撤熔断拦截</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟当日回撤达 3.5% (超过 3% 阈值) 时的开仓熔断</div>
                        </button>
                        <button onclick="testOrderScenario('normal')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-emerald-500/50 transition">
                            <div class="text-xs font-bold text-emerald-400">测试 4: 合规正常报单与模拟撮合</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟买入 0.1 BTC，体验全项放行、滑点扣除与 OMS 撮合成交</div>
                        </button>
                    </div>
                </div>

                <!-- Simulation Output -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-lg font-semibold text-white">OMS 订单执行与风控审计日志</h2>
                    <div id="order-audit-box" class="h-64 p-4 rounded-xl bg-slate-900/90 border border-slate-800 overflow-y-auto mono text-xs space-y-2 text-slate-300">
                        <div class="text-slate-500">[SYSTEM] OMS 撮合网关与风控管理器已连接就绪。</div>
                        <div class="text-slate-500">[READY] 等待测试场景触发...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="glass p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
            <div>
                <span class="text-slate-200 font-semibold">GeminiQuant 生产级架构:</span> OpenBB 数据枢纽 + System 2 TradingAgents + System 1 Laya + System 0 QIFI OMS
            </div>
            <div>
                托管在 Vercel Serverless · GitHub开源可审计
            </div>
        </footer>
    </div>

    <!-- Quick Modal -->
    <div id="quick-modal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="glass p-6 rounded-2xl max-w-md w-full border border-blue-500/40 space-y-4">
            <div class="flex items-center justify-between">
                <h3 class="text-base font-bold text-white flex items-center gap-2" id="modal-title">Laya 实时评估</h3>
                <button onclick="closeModal()" class="text-slate-400 hover:text-white">&times;</button>
            </div>
            <div id="modal-body" class="mono text-xs space-y-2"></div>
            <button onclick="closeModal()" class="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition">关闭窗口</button>
        </div>
    </div>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active', 'bg-blue-600', 'text-white'));
            document.getElementById(tabId).classList.remove('hidden');
            
            if (tabId === 'tab-markets') document.getElementById('btn-markets').classList.add('active');
            if (tabId === 'tab-laya') document.getElementById('btn-laya').classList.add('active');
            if (tabId === 'tab-research') document.getElementById('btn-research').classList.add('active');
            if (tabId === 'tab-risk') document.getElementById('btn-risk').classList.add('active');
        }

        async function updateLayaFromSliders() {
            const rsi = parseFloat(document.getElementById('input-rsi').value);
            const dd = parseFloat(document.getElementById('input-dd').value);
            const regime = document.getElementById('input-regime').value;
            const symbol = document.getElementById('input-symbol').value;

            document.getElementById('val-rsi').innerText = rsi;
            document.getElementById('val-dd').innerText = dd + '%';

            try {
                const res = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol, rsi, drawdown: dd, regime, price: 85980 })
                });
                const data = await res.json();

                document.getElementById('res-action').innerText = data.action;
                document.getElementById('res-urgency').innerText = data.urgency;
                document.getElementById('res-confidence').innerText = data.confidence + ' (' + (data.action_probability * 100).toFixed(1) + '%)';
                document.getElementById('res-risk').innerText = data.risk_passed ? 'TRUE (放行)' : 'FALSE (阻断)';
                document.getElementById('res-risk').className = data.risk_passed ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';
                document.getElementById('res-size').innerText = data.size_factor;
                document.getElementById('laya-latency-badge').innerText = '耗时: ' + data.latency_ms + ' ms';
            } catch (e) {
                console.error(e);
            }
        }

        async function runQuickEval(symbol, assetClass, price, rsi) {
            document.getElementById('modal-title').innerText = '⚡️ ' + symbol + ' 快速评估';
            document.getElementById('modal-body').innerHTML = '<div class="text-slate-400">正在调用 Laya 极速决策引擎...</div>';
            document.getElementById('quick-modal').classList.remove('hidden');

            try {
                const res = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol, asset_class: assetClass, price, rsi, drawdown: 0.5, regime: 'BULL_EXPANSION' })
                });
                const d = await res.json();
                document.getElementById('modal-body').innerHTML = `
                    <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5">
                        <div class="flex justify-between"><span class="text-slate-400">标的代码:</span><span class="text-white">${symbol}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">决策动作:</span><span class="text-emerald-400 font-bold">${d.action}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">执行紧迫度:</span><span class="text-blue-300">${d.urgency}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">前置风控初筛:</span><span class="${d.risk_passed ? 'text-emerald-400' : 'text-rose-400'}">${d.risk_passed ? '通过' : '否决'}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">决策推断耗时:</span><span class="text-yellow-400 font-bold">${d.latency_ms} ms</span></div>
                    </div>
                `;
            } catch(e) {
                document.getElementById('modal-body').innerText = '请求失败: ' + e;
            }
        }

        function closeModal() {
            document.getElementById('quick-modal').classList.add('hidden');
        }

        async function triggerResearchDebate() {
            const btn = document.getElementById('btn-run-debate');
            btn.innerText = '正在组织多智能体辩论...';
            try {
                const res = await fetch('/api/research', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol: 'AU2412' })
                });
                const d = await res.json();
                document.getElementById('deb-fund').innerText = d.analyst_reports.fundamental.summary;
                document.getElementById('deb-sent').innerText = d.analyst_reports.sentiment.summary;
                document.getElementById('deb-tech').innerText = d.analyst_reports.technical.summary;
                document.getElementById('deb-catalyst').innerText = '核心催化剂：' + d.catalyst;
                document.getElementById('deb-winner-badge').innerText = d.debate_winner + ' WINNER';
            } catch(e) {
                console.error(e);
            } finally {
                btn.innerText = '▶ 立即启动投研辩论';
            }
        }

        async function testOrderScenario(scenario) {
            const box = document.getElementById('order-audit-box');
            let req = {};
            if (scenario === 't_plus_1') {
                req = { symbol: '600519.SH', asset_class: 'EQUITY_CN', side: 'SELL', price: 51.20, volume: 100, test_scenario: 't_plus_1' };
            } else if (scenario === 'limit_up') {
                req = { symbol: '600519.SH', asset_class: 'EQUITY_CN', side: 'BUY', price: 1760.0, volume: 100, test_scenario: 'limit_up' };
            } else if (scenario === 'drawdown') {
                req = { symbol: 'BTC/USDT', asset_class: 'CRYPTO', side: 'BUY', price: 60000.0, volume: 0.5, test_scenario: 'drawdown' };
            } else {
                req = { symbol: 'BTC/USDT', asset_class: 'CRYPTO', side: 'BUY', price: 85980.0, volume: 0.1, test_scenario: 'normal' };
            }

            try {
                const res = await fetch('/api/order', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(req)
                });
                const d = await res.json();
                const ts = new Date().toLocaleTimeString();

                if (d.status === 'BLOCKED') {
                    box.innerHTML += `<div class="text-rose-400 font-semibold">[${ts}] ✕ 风控阻断: ${d.reason}</div>`;
                } else {
                    box.innerHTML += `<div class="text-emerald-400 font-semibold">[${ts}] ✓ 撮合成交: ${d.symbol} ${d.side} ${d.filled_volume}@${d.filled_price} (手续费: ${d.commission})</div>`;
                    if (d.account_equity) {
                        document.getElementById('kpi-equity').innerText = '¥ ' + d.account_equity.toLocaleString('zh-CN', {minimumFractionDigits: 2});
                    }
                }
                box.scrollTop = box.scrollHeight;
            } catch(e) {
                box.innerHTML += `<div class="text-rose-500">[ERROR] 模拟订单请求异常: ${e}</div>`;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """返回全新交互式玻璃拟态量化交易大盘 UI"""
    return DASHBOARD_HTML

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": "OmniQuant / GeminiQuant",
        "platform": "Vercel Serverless"
    }

@app.get("/api/status")
async def get_system_status():
    account = oms.get_account_snapshot()
    macro = research_memory.get_latest_context()
    return {
        "account": {
            "total_equity": account.total_equity,
            "available_cash": account.available_cash,
            "daily_drawdown_pct": round(account.daily_drawdown_pct, 2),
            "peak_drawdown_pct": round(account.current_drawdown_pct, 2),
            "positions_count": len(account.positions)
        },
        "system1_laya": {
            "model": "ModernBERT-large (421M)",
            "benchmark_latency_ms": 0.02,
            "type": "non-autoregressive",
            "hallucination": "zero"
        },
        "system2_tradingagents": macro
    }

@app.post("/api/evaluate")
async def evaluate_laya(req: EvaluateRequest):
    """在线交互运行 Laya 极速决策引擎"""
    asset_cls = getattr(AssetClass, req.asset_class, AssetClass.CRYPTO)
    tick = TickData(symbol=req.symbol, asset_class=asset_cls, last_price=req.price)
    tech = {"rsi": req.rsi, "macd_hist": 1.25, "bb_bandwidth": 0.045, "ofi": 0.42}
    macro = {"regime": req.regime, "debate_winner": "BULL", "sentiment": 0.75, "catalyst": "流动性改善"}
    account = oms.get_account_snapshot()
    # 注入模拟回撤用于测试
    account.daily_start_equity = 1000000.0
    account.total_equity = 1000000.0 * (1.0 - req.drawdown / 100.0)

    state = state_builder.build_state(tick, tech, macro, account)
    decision = laya_engine.evaluate(state)
    return {
        "symbol": req.symbol,
        "action": decision.action,
        "urgency": decision.urgency,
        "confidence": decision.confidence,
        "risk_passed": decision.risk_passed,
        "size_factor": decision.size_factor,
        "action_probability": decision.action_probability,
        "latency_ms": decision.latency_ms,
        "engine": decision.engine
    }

@app.post("/api/research")
async def run_research(payload: Dict[str, Any] = Body(...)):
    """在线运行 TradingAgents 多智能体辩论与研报共识"""
    symbol = payload.get("symbol", "AU2412")
    res = research_graph.run_committee_deliberation(symbol, {})
    return res

@app.post("/api/order")
async def simulate_order(req: SimulateOrderRequest):
    """在线测试 OMS 订单撮合与前置风控拦截"""
    asset_cls = getattr(AssetClass, req.asset_class, AssetClass.EQUITY_CN)
    side = OrderSide.SELL if req.side == "SELL" else OrderSide.BUY

    order = OrderRequest(
        symbol=req.symbol,
        asset_class=asset_cls,
        side=side,
        price=req.price,
        volume=req.volume
    )

    account = oms.get_account_snapshot()
    tick = None

    # 根据测试场景注入特定的风控边界
    if req.test_scenario == "limit_up":
        tick = TickData(symbol=req.symbol, asset_class=asset_cls, last_price=req.price, upper_limit_price=req.price)
    elif req.test_scenario == "drawdown":
        account.daily_start_equity = 1000000.0
        account.total_equity = 965000.0 # 3.5% 回撤
    elif req.test_scenario == "t_plus_1":
        # A 股持仓可用头寸为 0
        from core.models.order import Position
        account.positions[req.symbol] = Position(
            symbol=req.symbol, asset_class=asset_cls, side=OrderSide.BUY, volume=100.0, available_volume=0.0, avg_open_price=req.price, last_price=req.price
        )

    decision = laya_engine.evaluate(state_builder.build_state(
        TickData(symbol=req.symbol, asset_class=asset_cls, last_price=req.price),
        {"rsi": 50.0},
        research_memory.get_latest_context(),
        account
    ))

    passed, reason = risk_manager.check_pre_trade_risk(order, decision, account, tick)
    if not passed:
        return {"status": "BLOCKED", "reason": reason}

    report = await oms.submit_order(order)
    return {
        "status": "FILLED",
        "symbol": report.symbol,
        "side": report.side.value,
        "filled_price": report.filled_price,
        "filled_volume": report.filled_volume,
        "commission": report.commission,
        "account_equity": account.total_equity
    }
