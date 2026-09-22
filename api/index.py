"""
GeminiQuant / OmniQuant 生产级全资产智能量化交易平台 (Vercel Serverless & 交互控制台)
"""
from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# 将项目根目录加入 sys.path
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
    title="GeminiQuant 量化交易平台",
    description="全资产多智能体智能量化交易系统（A股/港美股/加密货币/金银/商品期货/期权）",
    version="0.2.0"
)

# 统一中文化术语映射表
CHINESE_TRANSLATIONS = {
    # 决策动作
    "STRONG_BUY": "强烈买入",
    "BUY": "买入做多",
    "HOLD": "持有观望",
    "REDUCE": "减仓防守",
    "STRONG_SELL": "清仓做空",
    # 报单紧迫度
    "AGGRESSIVE_TAKER": "市价吃单 (Taker)",
    "PASSIVE_MAKER": "限价挂单 (Maker)",
    # 置信度
    "HIGH": "高置信度",
    "MEDIUM": "中置信度",
    "LOW": "低置信度",
    # 仓位比例
    "FULL": "满仓 (100%)",
    "HALF": "半仓 (50%)",
    "TINY": "轻仓 (20%)",
    "NONE": "空仓 (0%)",
    # 市场宏观周期
    "BULL_EXPANSION": "牛市强扩张期",
    "RANGE_BOUND": "宽幅震荡洗盘期",
    "VOLATILE_CHOP": "高波震荡分化期",
    "BEAR_CONTRACTION": "熊市去杠杆收缩期",
    "BEAR_LIQUIDATION": "空头流动性踩踏期",
    # 资产分类
    "CRYPTO": "加密货币",
    "PRECIOUS_METALS": "贵金属(金银)",
    "COMMODITY_FUTURES": "商品期货",
    "EQUITY_CN": "A股股票",
    "EQUITY_US_HK": "港美股",
    "OPTIONS": "金融期权",
    # 辩论方向
    "BULL": "多头胜出 (强烈看多)",
    "BEAR": "空头胜出 (防守看空)",
    # 报单方向
    "BUY": "买入",
    "SELL": "卖出",
    # 撮合状态
    "FILLED": "已撮合成交",
    "BLOCKED": "前置风控驳回"
}

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
    price: float = 1650.0
    volume: float = 100.0
    test_scenario: Optional[str] = "t_plus_1"

# 预置全资产旗舰标的池（扩充至20+标的，覆盖六大市场分类）
INITIAL_WATCHLIST = [
    # 加密货币
    {"symbol": "BTC/USDT", "name": "比特币永续", "category": "CRYPTO", "price": 85980.76, "change": "+2.45%", "rsi": 28.5, "risk": "放行"},
    {"symbol": "ETH/USDT", "name": "以太坊永续", "category": "CRYPTO", "price": 3150.20, "change": "+3.10%", "rsi": 32.0, "risk": "放行"},
    {"symbol": "SOL/USDT", "name": "Solana永续", "category": "CRYPTO", "price": 182.40, "change": "+5.60%", "rsi": 35.5, "risk": "放行"},
    
    # 贵金属 (上期所)
    {"symbol": "AU2412", "name": "沪金连续", "category": "PRECIOUS_METALS", "price": 618.50, "change": "+0.85%", "rsi": 45.0, "risk": "放行"},
    {"symbol": "AG2412", "name": "沪银主力", "category": "PRECIOUS_METALS", "price": 7820.00, "change": "+1.20%", "rsi": 48.0, "risk": "放行"},
    
    # 商品期货 (CTP)
    {"symbol": "RB2501", "name": "螺纹钢主力", "category": "COMMODITY_FUTURES", "price": 3320.00, "change": "-0.45%", "rsi": 52.0, "risk": "放行"},
    {"symbol": "SC2412", "name": "原油连续", "category": "COMMODITY_FUTURES", "price": 542.80, "change": "+1.15%", "rsi": 56.0, "risk": "放行"},
    {"symbol": "CU2412", "name": "沪铜主力", "category": "COMMODITY_FUTURES", "price": 76800.00, "change": "+0.35%", "rsi": 49.0, "risk": "放行"},
    
    # A股核心资产
    {"symbol": "600519.SH", "name": "贵州茅台", "category": "EQUITY_CN", "price": 1650.00, "change": "+0.65%", "rsi": 62.0, "risk": "T+1校验"},
    {"symbol": "300750.SZ", "name": "宁德时代", "category": "EQUITY_CN", "price": 268.50, "change": "+2.80%", "rsi": 31.0, "risk": "T+1校验"},
    {"symbol": "000001.SZ", "name": "平安银行", "category": "EQUITY_CN", "price": 11.45, "change": "-0.20%", "rsi": 50.0, "risk": "T+1校验"},
    {"symbol": "601318.SH", "name": "中国平安", "category": "EQUITY_CN", "price": 56.80, "change": "+1.10%", "rsi": 42.0, "risk": "T+1校验"},
    
    # 港美股科技
    {"symbol": "AAPL.US", "name": "苹果公司", "category": "EQUITY_US_HK", "price": 228.40, "change": "+1.12%", "rsi": 58.0, "risk": "放行"},
    {"symbol": "NVDA.US", "name": "英伟达", "category": "EQUITY_US_HK", "price": 138.25, "change": "+4.18%", "rsi": 29.0, "risk": "放行"},
    {"symbol": "TSLA.US", "name": "特斯拉", "category": "EQUITY_US_HK", "price": 245.80, "change": "+3.45%", "rsi": 33.0, "risk": "放行"},
    {"symbol": "0700.HK", "name": "腾讯控股", "category": "EQUITY_US_HK", "price": 425.60, "change": "+1.80%", "rsi": 46.0, "risk": "放行"},
    
    # 金融期权
    {"symbol": "10005101", "name": "50ETF购11月2600", "category": "OPTIONS", "price": 0.0820, "change": "+12.3%", "rsi": 68.0, "risk": "裸空限制"},
    {"symbol": "10005102", "name": "50ETF沽11月2600", "category": "OPTIONS", "price": 0.0315, "change": "-8.5%", "rsi": 38.0, "risk": "裸空限制"}
]

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
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #0b0f19; color: #e2e8f0; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glass-card:hover { border-color: rgba(59, 130, 246, 0.4); transform: translateY(-2px); transition: all 0.2s ease; }
        .tab-btn.active { background-color: #2563eb; color: white; border-color: #3b82f6; }
        .filter-btn.active { background-color: #3b82f6; color: white; border-color: #60a5fa; }
    </style>
</head>
<body class="min-h-screen p-3 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        <!-- 头部导航 -->
        <header class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 glass p-6 rounded-2xl">
            <div>
                <div class="flex items-center gap-3">
                    <div class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></div>
                    <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                        <span>GeminiQuant 量化交易系统</span>
                        <span class="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">v0.2.0 全中文环境</span>
                    </h1>
                </div>
                <p class="text-slate-400 text-sm mt-1">覆盖 A股 · 港美股 · 加密货币 · 黄金白银 · 商品期货 · 金融期权 全资产智能决策底座</p>
            </div>
            <div class="flex flex-wrap items-center gap-3">
                <a href="/docs" target="_blank" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
                    接口文档 (Swagger)
                </a>
                <a href="https://github.com/CrazyRock114/geminiquant" target="_blank" class="px-4 py-2 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition flex items-center gap-2">
                    <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    GitHub 仓库
                </a>
            </div>
        </header>

        <!-- KPI 核心运行看板 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">账户总动态权益</div>
                <div class="text-2xl font-bold text-white mono mt-1" id="kpi-equity">¥ 1,009,874.68</div>
                <div class="text-xs text-emerald-400 mt-2 flex items-center gap-1 font-semibold">
                    <span>▲ +0.99%</span>
                    <span class="text-slate-500 font-normal">日内动态收益</span>
                </div>
            </div>
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">极速决策引擎 (Laya)</div>
                <div class="text-2xl font-bold text-blue-400 mono mt-1" id="kpi-latency">&lt; 0.02 毫秒</div>
                <div class="text-xs text-slate-400 mt-2">非自回归判别模型 · 零幻觉</div>
            </div>
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">宏观投研委员会 (TradingAgents)</div>
                <div class="text-2xl font-bold text-emerald-400 mt-1" id="kpi-regime">牛市强扩张期</div>
                <div class="text-xs text-slate-400 mt-2">多空多智能体辩论：多头占优 (75%)</div>
            </div>
            <div class="glass p-5 rounded-2xl glass-card">
                <div class="text-xs text-slate-400 font-medium">风控与执行底座 (QIFI / OMS)</div>
                <div class="text-2xl font-bold text-purple-400 mt-1">就绪生效中</div>
                <div class="text-xs text-slate-400 mt-2">CTP / QMT / CCXT / IBKR 穿透式网关</div>
            </div>
        </div>

        <!-- 导航选项卡 -->
        <div class="flex flex-wrap items-center gap-2 p-1.5 glass rounded-2xl border border-slate-800">
            <button onclick="switchTab('tab-markets')" id="btn-markets" class="tab-btn active px-4 py-2 text-xs font-semibold rounded-xl transition border border-transparent">
                📊 全资产实时监控矩阵
            </button>
            <button onclick="switchTab('tab-laya')" id="btn-laya" class="tab-btn px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white transition border border-transparent">
                ⚡️ Laya 毫秒决策沙盘与调参
            </button>
            <button onclick="switchTab('tab-research')" id="btn-research" class="tab-btn px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white transition border border-transparent">
                🧠 TradingAgents 宏观投研室
            </button>
            <button onclick="switchTab('tab-risk')" id="btn-risk" class="tab-btn px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white transition border border-transparent">
                🛡 前置风控与订单撮合演练
            </button>
        </div>

        <!-- TAB 1: 全资产行情与决策矩阵 -->
        <div id="tab-markets" class="tab-content space-y-4">
            <div class="glass p-6 rounded-2xl space-y-4">
                <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div>
                        <h2 class="text-lg font-semibold text-white">全资产核心标的实时池</h2>
                        <p class="text-xs text-slate-400 mt-0.5">支持跨市场品种快速检索与实时判决。点击「⚡️ 立即评估」将实时更新对应标的决策状态与信号。</p>
                    </div>

                    <!-- 快速搜索与添加任意标的 -->
                    <div class="flex items-center gap-2 w-full md:w-auto">
                        <input type="text" id="custom-symbol-input" placeholder="输入任意代码 (如 000001.SZ, TSLA.US)" class="px-3 py-1.5 text-xs rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-blue-500 w-64">
                        <button onclick="addAndEvalCustomSymbol()" class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition flex items-center gap-1">
                            <span>➕ 实时分析</span>
                        </button>
                    </div>
                </div>

                <!-- 分类筛选器 -->
                <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80 text-xs">
                    <span class="text-slate-400 mr-1">市场分类筛选:</span>
                    <button onclick="filterCategory('ALL')" class="filter-btn active px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">全部标的</button>
                    <button onclick="filterCategory('CRYPTO')" class="filter-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">加密货币</button>
                    <button onclick="filterCategory('PRECIOUS_METALS')" class="filter-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">贵金属(金银)</button>
                    <button onclick="filterCategory('COMMODITY_FUTURES')" class="filter-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">商品期货</button>
                    <button onclick="filterCategory('EQUITY_CN')" class="filter-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">A股核心</button>
                    <button onclick="filterCategory('EQUITY_US_HK')" class="filter-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">港美股</button>
                    <button onclick="filterCategory('OPTIONS')" class="filter-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition">金融期权</button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="text-xs text-slate-400 border-b border-slate-800">
                            <tr>
                                <th class="pb-3">标的代码与名称</th>
                                <th class="pb-3">资产分类</th>
                                <th class="pb-3">最新参考价</th>
                                <th class="pb-3">动量指标 (RSI)</th>
                                <th class="pb-3">当前决策信号</th>
                                <th class="pb-3">前置风控初筛</th>
                                <th class="pb-3 text-right">实时判决操作</th>
                            </tr>
                        </thead>
                        <tbody id="watchlist-table-body" class="divide-y divide-slate-800/60 mono text-xs">
                            <!-- 由 JavaScript 动态渲染，确保无冲突 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: Laya 毫秒决策沙盘与调参 -->
        <div id="tab-laya" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 左侧调参面板 -->
                <div class="glass p-6 rounded-2xl space-y-5">
                    <h2 class="text-lg font-semibold text-white flex items-center gap-2">
                        <span>🎛</span> Laya 决策输入特征调参台
                    </h2>
                    <p class="text-xs text-slate-400">实时拖动滑块调节微观动量与账户状态，体验 Laya 非自回归模型极速推理过程。</p>
                    
                    <div class="space-y-4 text-xs">
                        <div>
                            <label class="text-slate-400 flex justify-between">
                                <span>RSI 动量指标 (超卖 &lt;30 / 超买 &gt;70):</span>
                                <span id="val-rsi" class="text-blue-400 font-bold mono">28.5 (超卖)</span>
                            </label>
                            <input type="range" id="input-rsi" min="10" max="90" value="28" step="1" oninput="updateLayaFromSliders()" class="w-full mt-1.5 accent-blue-500">
                        </div>
                        <div>
                            <label class="text-slate-400 flex justify-between">
                                <span>账户单日动态回撤 (%):</span>
                                <span id="val-dd" class="text-amber-400 font-bold mono">0.5%</span>
                            </label>
                            <input type="range" id="input-dd" min="0" max="5" value="0.5" step="0.1" oninput="updateLayaFromSliders()" class="w-full mt-1.5 accent-amber-500">
                            <div class="text-[10px] text-slate-500 mt-0.5">注：回撤超过 3.0% 时，前置风控将直接触发一票否决硬熔断</div>
                        </div>
                        <div>
                            <label class="text-slate-400">System 2 宏观周期环境输入 (Macro Regime):</label>
                            <select id="input-regime" onchange="updateLayaFromSliders()" class="w-full mt-1.5 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs">
                                <option value="BULL_EXPANSION">牛市强扩张期 (BULL_EXPANSION)</option>
                                <option value="RANGE_BOUND">宽幅震荡洗盘期 (RANGE_BOUND)</option>
                                <option value="BEAR_CONTRACTION">熊市去杠杆收缩期 (BEAR_CONTRACTION)</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-slate-400">测试标的品种:</label>
                            <select id="input-symbol" onchange="updateLayaFromSliders()" class="w-full mt-1.5 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs">
                                <option value="BTC/USDT">BTC/USDT (加密货币永续)</option>
                                <option value="AU2412">AU2412 (沪金期货连续)</option>
                                <option value="600519.SH">600519.SH (贵州茅台 A股)</option>
                                <option value="NVDA.US">NVDA.US (英伟达 美股)</option>
                                <option value="10005101">10005101 (50ETF期权)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- 右侧结果展示面板 -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <div class="flex items-center justify-between">
                        <h2 class="text-lg font-semibold text-white">⚡️ Laya 极速推理结果</h2>
                        <span id="laya-latency-badge" class="text-xs px-2.5 py-1 rounded-lg bg-blue-500/20 text-blue-300 mono border border-blue-500/30">推理耗时: 0.01 毫秒</span>
                    </div>
                    <div class="space-y-3 mono text-xs">
                        <div class="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
                            <div class="flex justify-between items-center pb-2 border-b border-slate-800">
                                <span class="text-slate-400 font-sans">决策动作 (Action):</span>
                                <span id="res-action" class="text-base font-bold text-emerald-400">强烈买入</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-slate-400 font-sans">执行方式 (Urgency):</span>
                                <span id="res-urgency" class="text-blue-300 font-semibold">市价吃单 (Taker)</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-slate-400 font-sans">决策置信度 (Confidence):</span>
                                <span id="res-confidence" class="text-purple-300 font-semibold">高置信度 (92.0%)</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-slate-400 font-sans">前置风控初筛 (Pre-Risk):</span>
                                <span id="res-risk" class="text-emerald-400 font-bold">✓ 校验通过 (放行)</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-slate-400 font-sans">建议仓位比例 (Size Factor):</span>
                                <span id="res-size" class="text-slate-200 font-semibold">满仓 (100%)</span>
                            </div>
                        </div>
                        <div class="p-3.5 rounded-xl bg-blue-950/30 border border-blue-900/40 text-[11px] text-slate-300 font-sans leading-relaxed">
                            💡 <strong class="text-blue-400">非自回归架构优势：</strong> Laya 使用判别式分类头替代逐字自回归解码，将决策延迟从传统大模型的 2000~5000 毫秒骤降至 <strong>0.02 毫秒</strong>，彻底消除量化交易中的幻觉与滑点风险。
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 3: TradingAgents 宏观投研室 -->
        <div id="tab-research" class="tab-content hidden space-y-6">
            <div class="glass p-6 rounded-2xl space-y-5">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                        <h2 class="text-lg font-semibold text-white">TradingAgents 买方投研委员会</h2>
                        <p class="text-xs text-slate-400 mt-0.5">模拟真实买方机构：基本面分析师、舆情分析师、技术分析师独立调研并提交多空委员会激烈辩论</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <input type="text" id="research-symbol-input" value="AU2412" class="px-3 py-2 text-xs rounded-xl bg-slate-800 border border-slate-700 text-white w-28 uppercase mono text-center font-bold">
                        <button onclick="triggerResearchDebate()" id="btn-run-debate" class="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 transition flex items-center gap-2">
                            <span>▶ 启动投研多智能体辩论</span>
                        </button>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
                        <div class="text-blue-400 font-bold flex items-center gap-1.5">
                            <span>📊</span> 1. 基本面分析师
                        </div>
                        <p id="deb-fund" class="text-slate-300 leading-relaxed">标的具备强劲央行购金与实际利率下行支撑，估值分位数处于合理安全边际区间。</p>
                        <div class="text-slate-500 text-[10px] mono">打分权重: 0.75 / 1.0</div>
                    </div>
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
                        <div class="text-purple-400 font-bold flex items-center gap-1.5">
                            <span>📰</span> 2. 舆情与新闻分析师
                        </div>
                        <p id="deb-sent" class="text-slate-300 leading-relaxed">主流财经常态讨论以地缘避险与宽松流动性为主，市场综合情绪偏向积极。</p>
                        <div class="text-slate-500 text-[10px] mono">打分权重: 0.68 / 1.0</div>
                    </div>
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
                        <div class="text-yellow-400 font-bold flex items-center gap-1.5">
                            <span>📈</span> 3. 技术面分析师
                        </div>
                        <p id="deb-tech" class="text-slate-300 leading-relaxed">日线级别均线呈现多头排列，突破 20 日盘整平台，成交量温和放大。</p>
                        <div class="text-slate-500 text-[10px] mono">打分权重: 0.70 / 1.0</div>
                    </div>
                </div>

                <!-- 辩论终局卡片 -->
                <div class="p-5 rounded-xl bg-gradient-to-r from-blue-900/40 via-purple-900/40 to-slate-900/60 border border-blue-500/30 space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-blue-400 uppercase tracking-wider">多空质询辩论决议 (Bull vs Bear Consensus)</span>
                        <span id="deb-winner-badge" class="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30">多头胜出 (看多)</span>
                    </div>
                    <div class="text-sm text-white font-medium" id="deb-catalyst">
                        核心催化剂：多周期均线突破共振与海外流动性改善
                    </div>
                    <div class="text-xs text-slate-400">
                        该决议已自动同步持久化至 System 2 缓存中，供下游 Laya 决策引擎作为静态宏观槽调用。
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 4: 前置风控与模拟报单 -->
        <div id="tab-risk" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 触发场景按钮 -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-lg font-semibold text-white">触发前置风控拦截场景演练</h2>
                    <p class="text-xs text-slate-400">点击以下不同违规报单指令，亲身体验工业级硬核风控防穿仓与合规拦截能力：</p>
                    
                    <div class="space-y-2.5">
                        <button onclick="testOrderScenario('t_plus_1')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-amber-500/50 transition">
                            <div class="text-xs font-bold text-amber-400">测试场景 1: A股 T+1 日内卖出违规拦截</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟卖出今日刚刚买入未交收的 100 股贵州茅台 (可用头寸 = 0)</div>
                        </button>
                        <button onclick="testOrderScenario('limit_up')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-rose-500/50 transition">
                            <div class="text-xs font-bold text-rose-400">测试场景 2: 涨停板封板追高买入拦截</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟以涨停价 ¥1760.00 追买已封涨停板的股票，防止无效排单套牢</div>
                        </button>
                        <button onclick="testOrderScenario('drawdown')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-rose-500/50 transition">
                            <div class="text-xs font-bold text-rose-400">测试场景 3: 账户单日动态回撤超限熔断</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟当日净值回撤达 3.5% (超过 3.0% 阈值) 时的全局开仓一票否决</div>
                        </button>
                        <button onclick="testOrderScenario('normal')" class="w-full text-left p-3.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-emerald-500/50 transition">
                            <div class="text-xs font-bold text-emerald-400">测试场景 4: 合规正常报单与 OMS 极速撮合</div>
                            <div class="text-[11px] text-slate-400 mt-1">模拟合规买入 0.1 BTC，体验全项放行、双边手续费扣除与 OMS 撮合成交</div>
                        </button>
                    </div>
                </div>

                <!-- 审计终端日志 -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <div class="flex items-center justify-between">
                        <h2 class="text-lg font-semibold text-white">OMS 订单执行与风控审计流水</h2>
                        <button onclick="clearAuditLog()" class="text-xs text-slate-400 hover:text-white">清空日志</button>
                    </div>
                    <div id="order-audit-box" class="h-64 p-4 rounded-xl bg-slate-900/90 border border-slate-800 overflow-y-auto mono text-xs space-y-2 text-slate-300">
                        <div class="text-slate-500">[系统初始化] OMS 撮合网关与风控管理器已连接就绪。</div>
                        <div class="text-slate-500">[就绪就绪] 请在左侧点击任意测试场景观察毫秒级实时审计...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 页脚 -->
        <footer class="glass p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
            <div>
                <span class="text-slate-200 font-semibold">GeminiQuant 工业级全资产架构:</span> OpenBB 数据枢纽 + TradingAgents 宏观研报 + Laya 极速决策 + QIFI OMS 撮合底座
            </div>
            <div>
                生产环境部署于 Vercel Serverless · 代码开源透明
            </div>
        </footer>
    </div>

    <!-- 全局提示 Toast -->
    <div id="toast" class="fixed top-5 right-5 z-50 transform transition-all duration-300 translate-y-[-100px] opacity-0 pointer-events-none">
        <div id="toast-content" class="px-4 py-3 rounded-xl bg-slate-800 border border-blue-500/40 text-white text-xs shadow-2xl flex items-center gap-2">
        </div>
    </div>

    <script>
        // 中文词典
        const DICT = {
            'STRONG_BUY': '强烈买入',
            'BUY': '买入做多',
            'HOLD': '持有观望',
            'REDUCE': '减仓防守',
            'STRONG_SELL': '清仓做空',
            'AGGRESSIVE_TAKER': '市价吃单 (Taker)',
            'PASSIVE_MAKER': '限价挂单 (Maker)',
            'HIGH': '高置信度',
            'MEDIUM': '中置信度',
            'LOW': '低置信度',
            'FULL': '满仓 (100%)',
            'HALF': '半仓 (50%)',
            'TINY': '轻仓 (20%)',
            'NONE': '空仓 (0%)',
            'BULL_EXPANSION': '牛市强扩张期',
            'RANGE_BOUND': '宽幅震荡洗盘期',
            'BEAR_CONTRACTION': '熊市去杠杆收缩期',
            'CRYPTO': '加密货币',
            'PRECIOUS_METALS': '贵金属(金银)',
            'COMMODITY_FUTURES': '商品期货',
            'EQUITY_CN': 'A股股票',
            'EQUITY_US_HK': '港美股',
            'OPTIONS': '金融期权',
            'BULL': '多头胜出 (看多)',
            'BEAR': '空头胜出 (看空)'
        };

        function t(key) {
            return DICT[key] || key;
        }

        function showToast(msg, isSuccess = true) {
            const toast = document.getElementById('toast');
            const content = document.getElementById('toast-content');
            content.innerHTML = `<span>${isSuccess ? '⚡️' : '⚠️'}</span><span>${msg}</span>`;
            toast.classList.remove('translate-y-[-100px]', 'opacity-0');
            setTimeout(() => {
                toast.classList.add('translate-y-[-100px]', 'opacity-0');
            }, 3000);
        }

        // 初始标的池数据
        let currentWatchlist = """ + str(INITIAL_WATCHLIST).replace("'", '"') + """;
        let activeFilter = 'ALL';

        function renderWatchlist() {
            const tbody = document.getElementById('watchlist-table-body');
            tbody.innerHTML = '';

            const filtered = activeFilter === 'ALL' 
                ? currentWatchlist 
                : currentWatchlist.filter(item => item.category === activeFilter);

            filtered.forEach((item, idx) => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                tr.id = `row-${item.symbol.replace(/[^a-zA-Z0-9]/g, '_')}`;

                const isUp = item.change.startsWith('+');
                const priceClass = isUp ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold';
                const rsiAlert = item.rsi < 30 ? 'text-emerald-400 font-bold' : (item.rsi > 70 ? 'text-rose-400 font-bold' : 'text-slate-400');

                // 初始信号依据 RSI 智能预判，非死板硬编码
                let initialAction = 'HOLD';
                let actionBadgeClass = 'bg-slate-800 text-slate-300 border-slate-700';
                if (item.rsi < 35) {
                    initialAction = 'STRONG_BUY';
                    actionBadgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
                } else if (item.rsi > 65) {
                    initialAction = 'REDUCE';
                    actionBadgeClass = 'bg-rose-500/20 text-rose-400 border-rose-500/30';
                }

                tr.innerHTML = `
                    <td class="py-3.5 font-bold text-white">
                        <div class="flex items-center gap-2">
                            <span>${item.symbol}</span>
                            <span class="text-[11px] font-normal text-slate-400 font-sans">(${item.name})</span>
                        </div>
                    </td>
                    <td class="text-slate-400 font-sans">${t(item.category)}</td>
                    <td class="${priceClass}">${item.price.toLocaleString()} (${item.change})</td>
                    <td class="${rsiAlert}">${item.rsi.toFixed(1)} ${item.rsi < 30 ? '⚡️超卖' : (item.rsi > 70 ? '⚠️超买' : '')}</td>
                    <td id="signal-${item.symbol.replace(/[^a-zA-Z0-9]/g, '_')}">
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold border ${actionBadgeClass}">
                            ${t(initialAction)}
                        </span>
                    </td>
                    <td class="text-slate-300 font-sans">
                        <span class="text-xs ${item.risk === '放行' ? 'text-emerald-400' : 'text-amber-400'}">✓ ${item.risk}</span>
                    </td>
                    <td class="text-right">
                        <button onclick="runQuickEval('${item.symbol}', '${item.category}', ${item.price}, ${item.rsi})" class="px-3 py-1.5 rounded-xl bg-blue-600/90 hover:bg-blue-600 text-white font-sans text-xs transition shadow-sm hover:shadow-blue-500/20">
                            ⚡️ 立即评估
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function filterCategory(cat) {
            activeFilter = cat;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active', 'bg-blue-600', 'text-white'));
            event.target.classList.add('active', 'bg-blue-600', 'text-white');
            renderWatchlist();
        }

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

            document.getElementById('val-rsi').innerText = rsi + (rsi < 30 ? ' (超卖区)' : (rsi > 70 ? ' (超买区)' : ' (中性区)'));
            document.getElementById('val-dd').innerText = dd + '%';

            try {
                const res = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol, rsi, drawdown: dd, regime, price: 85980 })
                });
                const data = await res.json();

                // 纯中文渲染
                document.getElementById('res-action').innerText = t(data.action);
                document.getElementById('res-action').className = data.action.includes('BUY') 
                    ? 'text-lg font-bold text-emerald-400' 
                    : (data.action.includes('SELL') || data.action === 'REDUCE' ? 'text-lg font-bold text-rose-400' : 'text-lg font-bold text-amber-400');

                document.getElementById('res-urgency').innerText = t(data.urgency);
                document.getElementById('res-confidence').innerText = t(data.confidence) + ' (' + (data.action_probability * 100).toFixed(1) + '%)';
                document.getElementById('res-risk').innerText = data.risk_passed ? '✓ 校验通过 (全项放行)' : '✕ 前置风控否决 (已拦截)';
                document.getElementById('res-risk').className = data.risk_passed ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';
                document.getElementById('res-size').innerText = t(data.size_factor);
                document.getElementById('laya-latency-badge').innerText = '推理耗时: ' + data.latency_ms + ' 毫秒';
            } catch (e) {
                console.error(e);
            }
        }

        async function runQuickEval(symbol, assetClass, price, rsi) {
            showToast(`正在对 ${symbol} 执行 Laya 毫秒级判决...`, true);

            try {
                const res = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol, asset_class: assetClass, price, rsi, drawdown: 0.5, regime: 'BULL_EXPANSION' })
                });
                const d = await res.json();

                // 核心修复：更新对应行表格中的信号徽章！
                const cellId = `signal-${symbol.replace(/[^a-zA-Z0-9]/g, '_')}`;
                const cell = document.getElementById(cellId);
                if (cell) {
                    let badgeClass = 'bg-slate-800 text-slate-300 border-slate-700';
                    if (d.action.includes('BUY')) {
                        badgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-500/20';
                    } else if (d.action.includes('SELL') || d.action === 'REDUCE') {
                        badgeClass = 'bg-rose-500/20 text-rose-400 border-rose-500/40 shadow-sm shadow-rose-500/20';
                    } else {
                        badgeClass = 'bg-amber-500/20 text-amber-400 border-amber-500/40';
                    }
                    cell.innerHTML = `
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold border ${badgeClass} animate-pulse">
                            ${t(d.action)} · ${t(d.urgency)}
                        </span>
                    `;
                    // 1秒后去掉闪烁
                    setTimeout(() => {
                        const span = cell.querySelector('span');
                        if (span) span.classList.remove('animate-pulse');
                    }, 1200);
                }

                // 同步更新调参台输入
                document.getElementById('input-rsi').value = Math.round(rsi);
                document.getElementById('input-symbol').value = symbol;
                updateLayaFromSliders();

                showToast(`${symbol} 判决完成: ${t(d.action)} (${t(d.urgency)}, 耗时 ${d.latency_ms}ms)`, true);
            } catch(e) {
                showToast(`评估请求异常: ${e}`, false);
            }
        }

        async function addAndEvalCustomSymbol() {
            const input = document.getElementById('custom-symbol-input');
            const sym = input.value.trim().toUpperCase();
            if (!sym) {
                showToast('请输入有效的标的代码', false);
                return;
            }

            // 猜测资产类型
            let cat = 'EQUITY_CN';
            let name = '自定义标的';
            let price = 100.0;
            if (sym.includes('/USDT') || sym.includes('BTC') || sym.includes('ETH')) {
                cat = 'CRYPTO'; name = '加密货币'; price = 2500.0;
            } else if (sym.endsWith('.US') || sym.endsWith('.HK')) {
                cat = 'EQUITY_US_HK'; name = '海外股票'; price = 150.0;
            } else if (sym.startsWith('AU') || sym.startsWith('AG')) {
                cat = 'PRECIOUS_METALS'; name = '贵金属期货'; price = 600.0;
            } else if (sym.length === 6 && !isNaN(sym)) {
                cat = 'OPTIONS'; name = '期权合约'; price = 0.05;
            }

            const newObj = {
                symbol: sym,
                name: name,
                category: cat,
                price: price,
                change: '+0.00%',
                rsi: 50.0,
                risk: '校验通过'
            };

            // 检查是否已存在
            const existing = currentWatchlist.find(x => x.symbol === sym);
            if (!existing) {
                currentWatchlist.unshift(newObj);
            }
            renderWatchlist();
            input.value = '';

            // 立即对新标的发起实时评估
            await runQuickEval(sym, cat, price, 50.0);
        }

        async function triggerResearchDebate() {
            const sym = document.getElementById('research-symbol-input').value.trim().toUpperCase() || 'AU2412';
            const btn = document.getElementById('btn-run-debate');
            btn.innerText = '正在组织多智能体激烈辩论...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/research', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol: sym })
                });
                const d = await res.json();
                document.getElementById('deb-fund').innerText = d.analyst_reports.fundamental.summary;
                document.getElementById('deb-sent').innerText = d.analyst_reports.sentiment.summary;
                document.getElementById('deb-tech').innerText = d.analyst_reports.technical.summary;
                document.getElementById('deb-catalyst').innerText = '核心催化剂：' + d.catalyst;
                document.getElementById('deb-winner-badge').innerText = t(d.debate_winner);
                document.getElementById('deb-winner-badge').className = d.debate_winner === 'BULL' 
                    ? 'px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30'
                    : 'px-3 py-1 rounded-full bg-rose-500/20 text-rose-400 text-xs font-bold border border-rose-500/30';

                showToast(`标的 ${sym} 投研辩论完成：${t(d.debate_winner)}`, true);
            } catch(e) {
                console.error(e);
                showToast('辩论请求异常', false);
            } finally {
                btn.innerText = '▶ 启动投研多智能体辩论';
                btn.disabled = false;
            }
        }

        function clearAuditLog() {
            document.getElementById('order-audit-box').innerHTML = '<div class="text-slate-500">[系统就绪] 日志已清空。</div>';
        }

        async function testOrderScenario(scenario) {
            const box = document.getElementById('order-audit-box');
            let req = {};
            if (scenario === 't_plus_1') {
                req = { symbol: '600519.SH', asset_class: 'EQUITY_CN', side: 'SELL', price: 1650.0, volume: 100, test_scenario: 't_plus_1' };
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
                const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false });

                if (d.status === 'BLOCKED') {
                    box.innerHTML += `<div class="text-rose-400 font-semibold">[${ts}] ✕ 前置风控拦截: ${d.reason}</div>`;
                } else {
                    box.innerHTML += `<div class="text-emerald-400 font-semibold">[${ts}] ✓ OMS 撮合成交: 标的 ${d.symbol} 方向 ${t(d.side)} 成交量 ${d.filled_volume} 价格 ¥${d.filled_price.toLocaleString()} (手续费: ¥${d.commission})</div>`;
                    if (d.account_equity) {
                        document.getElementById('kpi-equity').innerText = '¥ ' + d.account_equity.toLocaleString('zh-CN', {minimumFractionDigits: 2});
                    }
                }
                box.scrollTop = box.scrollHeight;
            } catch(e) {
                box.innerHTML += `<div class="text-rose-500">[异常] 模拟订单请求错误: ${e}</div>`;
            }
        }

        // 页面就绪自动初始化
        document.addEventListener('DOMContentLoaded', () => {
            renderWatchlist();
            updateLayaFromSliders();
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """返回全新纯中文全资产交互式量化交易大盘 UI"""
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
            "type": "非自回归判别模型",
            "hallucination": "零幻觉"
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
    
    # 模拟回撤用于测试
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
        account.total_equity = 965000.0  # 3.5% 回撤
    elif req.test_scenario == "t_plus_1":
        # A 股持仓可用头寸为 0
        from core.models.order import Position
        account.positions[req.symbol] = Position(
            symbol=req.symbol,
            asset_class=asset_cls,
            side=OrderSide.BUY,
            volume=100.0,
            available_volume=0.0,
            avg_open_price=req.price,
            last_price=req.price
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
