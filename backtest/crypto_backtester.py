"""
OmniQuant Crypto Backtester Engine
High-precision vectorized and event-driven backtesting for cryptocurrency pairs.
Supports leverage, long/short positions, Binance fee tiers, slippage, and comprehensive risk metrics.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from backtest.strategies import BaseStrategy, StrategyRegistry, LayaMomentumStrategy

class CryptoBacktester:
    """加密资产回测执行引擎"""

    def __init__(
        self,
        strategy: Optional[BaseStrategy] = None,
        initial_capital: float = 100000.0,
        leverage: float = 1.0,
        taker_fee_rate: float = 0.0005, # 0.05% 币安标准 Taker 费率
        maker_fee_rate: float = 0.0002, # 0.02% 币安标准 Maker 费率
        slippage_bps: float = 5.0,      # 5 bps = 0.05% 滑点
        allow_short: bool = True
    ):
        self.strategy = strategy or LayaMomentumStrategy()
        self.initial_capital = float(initial_capital)
        self.leverage = max(1.0, float(leverage))
        self.taker_fee_rate = float(taker_fee_rate)
        self.maker_fee_rate = float(maker_fee_rate)
        self.slippage = float(slippage_bps) / 10000.0
        self.allow_short = allow_short

    def run(self, df: pd.DataFrame, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        """
        在给定的 OHLCV 数据上执行回测并生成评估报告
        """
        if df.empty or len(df) < 10:
            raise ValueError(f"回测数据不足，至少需要 10 根 K 线，当前仅有 {len(df)} 根")

        df = df.copy()
        signals = self.strategy.generate_signals(df)
        df["signal"] = signals

        capital = self.initial_capital
        position_side = 0 # 0: 空仓, 1: 多头, -1: 空头
        position_volume = 0.0
        entry_price = 0.0
        entry_time = None
        total_fees = 0.0

        equity_curve: List[Dict[str, Any]] = []
        trades: List[Dict[str, Any]] = []
        trade_id = 0

        first_close = df.iloc[0]["close"]
        peak_equity = capital

        for i in range(len(df)):
            row = df.iloc[i]
            cur_time = row["timestamp"]
            cur_price = row["close"]
            sig = row["signal"]

            # 如果不允许做空，将 -1 信号视为空仓离场 (0)
            target_side = sig
            if not self.allow_short and target_side < 0:
                target_side = 0

            # 检查是否有换仓需求
            if target_side != position_side:
                # 1. 先平掉已有持仓
                if position_side != 0:
                    exit_price = cur_price * (1.0 - self.slippage) if position_side == 1 else cur_price * (1.0 + self.slippage)
                    nominal = exit_price * position_volume
                    fee = nominal * self.taker_fee_rate
                    total_fees += fee

                    # 核算毛盈亏与净盈亏
                    if position_side == 1:
                        gross_pnl = (exit_price - entry_price) * position_volume
                    else:
                        gross_pnl = (entry_price - exit_price) * position_volume

                    net_pnl = gross_pnl - fee
                    capital += net_pnl
                    return_pct = (net_pnl / (entry_price * position_volume / self.leverage)) * 100.0 if entry_price > 0 else 0.0

                    trade_id += 1
                    trades.append({
                        "trade_id": trade_id,
                        "side": "做多 (LONG)" if position_side == 1 else "做空 (SHORT)",
                        "entry_time": entry_time.strftime("%Y-%m-%d %H:%M") if hasattr(entry_time, "strftime") else str(entry_time),
                        "exit_time": cur_time.strftime("%Y-%m-%d %H:%M") if hasattr(cur_time, "strftime") else str(cur_time),
                        "entry_price": round(entry_price, 2 if entry_price > 10 else 4),
                        "exit_price": round(exit_price, 2 if exit_price > 10 else 4),
                        "volume": round(position_volume, 4),
                        "gross_pnl": round(gross_pnl, 2),
                        "fee": round(fee, 2),
                        "net_pnl": round(net_pnl, 2),
                        "return_pct": round(return_pct, 2)
                    })

                    position_side = 0
                    position_volume = 0.0

                # 2. 开立新仓
                if target_side != 0 and capital > 100:
                    fill_price = cur_price * (1.0 + self.slippage) if target_side == 1 else cur_price * (1.0 - self.slippage)
                    # 可用资金按杠杆计算头寸名义价值 (留 2% 资金作为费率缓冲)
                    alloc_capital = capital * 0.98 * self.leverage
                    position_volume = alloc_capital / fill_price
                    entry_price = fill_price
                    entry_time = cur_time
                    position_side = target_side

                    # 扣除开仓手续费
                    fee = (position_volume * entry_price) * self.taker_fee_rate
                    capital -= fee
                    total_fees += fee

            # 计算当前 Bar 结束时的动态净值 (Mark-to-Market Equity)
            unrealized_pnl = 0.0
            if position_side == 1:
                unrealized_pnl = (cur_price - entry_price) * position_volume
            elif position_side == -1:
                unrealized_pnl = (entry_price - cur_price) * position_volume

            current_equity = capital + unrealized_pnl
            if current_equity > peak_equity:
                peak_equity = current_equity

            drawdown = (current_equity - peak_equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
            benchmark_equity = self.initial_capital * (cur_price / first_close)

            time_str = cur_time.strftime("%Y-%m-%d %H:%M") if hasattr(cur_time, "strftime") else str(cur_time)
            equity_curve.append({
                "time": time_str,
                "strategy_equity": round(current_equity, 2),
                "benchmark_equity": round(benchmark_equity, 2),
                "drawdown_pct": round(drawdown, 2),
                "price": round(cur_price, 2 if cur_price > 10 else 4)
            })

        # 回测结束强制平仓结算最后一笔持仓（若有）
        if position_side != 0:
            last_price = df.iloc[-1]["close"]
            exit_price = last_price * (1.0 - self.slippage) if position_side == 1 else last_price * (1.0 + self.slippage)
            fee = (position_volume * exit_price) * self.taker_fee_rate
            total_fees += fee
            if position_side == 1:
                net_pnl = (exit_price - entry_price) * position_volume - fee
            else:
                net_pnl = (entry_price - exit_price) * position_volume - fee
            capital += net_pnl
            trade_id += 1
            trades.append({
                "trade_id": trade_id,
                "side": "做多 (LONG)" if position_side == 1 else "做空 (SHORT)",
                "entry_time": entry_time.strftime("%Y-%m-%d %H:%M") if hasattr(entry_time, "strftime") else str(entry_time),
                "exit_time": df.iloc[-1]["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "volume": round(position_volume, 4),
                "gross_pnl": round(net_pnl + fee, 2),
                "fee": round(fee, 2),
                "net_pnl": round(net_pnl, 2),
                "return_pct": round((net_pnl / (entry_price * position_volume / self.leverage)) * 100.0, 2)
            })

        # 计算核心量化绩效统计指标
        final_equity = equity_curve[-1]["strategy_equity"]
        total_return_pct = (final_equity - self.initial_capital) / self.initial_capital * 100.0

        # 计算最大回撤
        drawdowns = [p["drawdown_pct"] for p in equity_curve]
        max_drawdown_pct = abs(min(drawdowns)) if drawdowns else 0.0

        # 计算日度收益率序列用于夏普与索提诺比率
        equities = pd.Series([p["strategy_equity"] for p in equity_curve])
        returns = equities.pct_change().dropna()
        daily_mean = returns.mean()
        daily_std = returns.std()
        downside_std = returns[returns < 0].std()

        sharpe = (daily_mean / daily_std * np.sqrt(365)) if daily_std > 0 else 0.0
        sortino = (daily_mean / downside_std * np.sqrt(365)) if downside_std > 0 else 0.0
        calmar = (total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0

        # 胜率与盈亏比
        win_trades = [t for t in trades if t["net_pnl"] > 0]
        loss_trades = [t for t in trades if t["net_pnl"] <= 0]
        win_rate_pct = (len(win_trades) / len(trades) * 100.0) if trades else 0.0

        gross_profit = sum(t["net_pnl"] for t in win_trades)
        gross_loss = abs(sum(t["net_pnl"] for t in loss_trades))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        benchmark_return_pct = (df.iloc[-1]["close"] - first_close) / first_close * 100.0

        # 如果曲线数据点过多，降采样至最多 150 个点供前端轻量化绘制
        step = max(1, len(equity_curve) // 150)
        sampled_curve = equity_curve[::step]
        if equity_curve and (not sampled_curve or sampled_curve[-1] != equity_curve[-1]):
            sampled_curve.append(equity_curve[-1])

        return {
            "symbol": symbol,
            "strategy_name": self.strategy.name,
            "period_bars": len(df),
            "start_time": df.iloc[0]["timestamp"].strftime("%Y-%m-%d %H:%M") if hasattr(df.iloc[0]["timestamp"], "strftime") else str(df.iloc[0]["timestamp"]),
            "end_time": df.iloc[-1]["timestamp"].strftime("%Y-%m-%d %H:%M") if hasattr(df.iloc[-1]["timestamp"], "strftime") else str(df.iloc[-1]["timestamp"]),
            "metrics": {
                "initial_capital": self.initial_capital,
                "final_equity": round(final_equity, 2),
                "total_return_pct": round(total_return_pct, 2),
                "benchmark_return_pct": round(benchmark_return_pct, 2),
                "alpha_pct": round(total_return_pct - benchmark_return_pct, 2),
                "max_drawdown_pct": round(max_drawdown_pct, 2),
                "sharpe_ratio": round(sharpe, 2),
                "sortino_ratio": round(sortino, 2),
                "calmar_ratio": round(calmar, 2),
                "win_rate_pct": round(win_rate_pct, 2),
                "profit_factor": round(profit_factor, 2),
                "total_trades": len(trades),
                "win_trades": len(win_trades),
                "loss_trades": len(loss_trades),
                "total_fees_paid": round(total_fees, 2),
                "leverage": self.leverage
            },
            "equity_curve": sampled_curve,
            "trades": trades[-50:] # 返回最近 50 笔成交记录
        }
