# OmniQuant 全资产智能量化交易系统

> 覆盖 **A股、港美股、Crypto、黄金白银（贵金属）、商品期货、期权** 的全资产多智能体量化系统。

---

## 核心架构设计：“双脑协同 + 执行底座”

```
+-----------------------------------------------------------------------------------+
|               Layer 1: 统一数据与特征总线 (Data & Feature Engine)                   |
|     - OpenBB Platform: 全球股票 / 宏观 (FRED) / 外汇 / 美股期权 / 现货金银          |
|     - 国内数据源: A股行情 / CTP 期货柜台 (AU/AG/RB) / 50ETF 期权                   |
|     - Crypto: CCXT 24/7 实时 Ticker / L2 订单簿 / 永续资金费率                      |
|     - Feature Engine: RSI / MACD / 布林带 / OFI 订单流不平衡度 / Black-Scholes Greeks |
+-----------------------------------------------------------------------------------+
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
+-----------------------------------+           +-----------------------------------+
| Layer 2: 宏观研报层 (System 2)    |           | Layer 3: 极速决策引擎 (System 1)  |
|      TradingAgents (LangGraph)    |           |            Laya / Jev             |
| - 基本面分析师 / 舆情新闻分析师   | 异步研报  | - 非自回归判别模型 (ModernBERT)   |
| - 技术分析师 / 多空博弈辩论       | ───────>  | - 推理耗时 < 35ms                 |
| - 输出宏观周期标签与催化剂        | 定时更新  | - 信号仲裁打分 + 前置一票否决风控 |
+-----------------------------------+           +-----------------------------------+
                                                                 │
                                                                 ▼
                                                +-----------------------------------+
                                                | Layer 4: 执行与风控底座 (System 0)|
                                                |          QUANTAXIS / QIFI         |
                                                | - 双重前置风控拦截 (Pre-Trade Guard)|
                                                | - A股 T+1 / 涨跌停 / 期权裸空保护 |
                                                | - 统一 OMS 订单路由与头寸核算     |
                                                | - CTP / QMT / IBKR / CCXT 网关    |
                                                +-----------------------------------+
```

---

## 快速上手与运行

### 1. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 2. 运行演示模式 (Demo Mode)
执行全资产类别（A股、美股、Crypto、沪金、螺纹钢、50ETF期权）的完整循环模拟撮合：
```bash
python main.py --mode demo
```

### 3. 基准测试 Laya 推理延迟 (Benchmark Mode)
评估 Laya 极速决策引擎在本地硬件（Apple Silicon MPS / CPU）下的单次推理耗时：
```bash
python main.py --mode benchmark
```

### 4. 运行 System 2 TradingAgents 多智能体研报 (Research Mode)
触发基本面分析师、技术分析师、舆情分析师与多空委员会辩论：
```bash
python main.py --mode research
```

### 5. 运行完整自动化测试套件
```bash
python -m unittest discover tests
```
