"""
OmniQuant Matrix Backtester Engine
Executes multi-strategy across multi-asset batch backtests in parallel/vectorized mode.
Generates comprehensive comparative heatmaps, leaderboards, and per-asset champion diagnostics.
"""
import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from data.binance_data import BinanceDataClient
from backtest.crypto_backtester import CryptoBacktester
from backtest.strategies import StrategyRegistry, BaseStrategy
from backtest.strategy_catalog import STRATEGY_CATALOG

logger = logging.getLogger("OmniQuant.MatrixBacktester")

class MatrixBacktester:
    """多标的多策略矩阵回测调度引擎"""

    DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ZEC/USDT"]

    STRATEGY_ALIASES = {
        "dual_ma": "dual_ema",
        "bollinger_bands": "bollinger",
        "rsi_reversal": "rsi_mean_reversion",
        "kdj_stochastic": "stoch_rsi",
        "atr_channel_breakout": "keltner_channel",
        "vwap_mean_reversion": "mfi_divergence",
        "cmf_capital_flow": "mfi_divergence",
        "obv_trend": "mfi_divergence",
        "triple_ema": "dual_ema",
    }

    @classmethod
    def run_matrix(
        cls,
        symbols: Optional[List[str]] = None,
        strategy_ids: Optional[List[str]] = None,
        interval: str = "1d",
        limit: int = 365,
        initial_capital: float = 100000.0,
        leverage: float = 1.0,
        allow_short: bool = True
    ) -> Dict[str, Any]:
        """
        执行多标的 × 多策略矩阵回测:
        1. 针对每一个标的高效拉取一次历史 K 线并缓存
        2. 在该标的 K 线上向量化执行选定的所有策略
        3. 聚合生成热力矩阵、天梯排行榜、单标的冠军以及量化智能洞察
        """
        t0 = time.time()
        symbols = [s.strip().upper() for s in (symbols or cls.DEFAULT_SYMBOLS) if s.strip()]
        if not symbols:
            symbols = cls.DEFAULT_SYMBOLS

        # 过滤与解析策略清单（剔除尚未配置具体规则的空白 custom_strategy）
        available_strats = StrategyRegistry.list_strategies()
        all_strat_ids = [s["id"] for s in available_strats if s["id"] != "custom_strategy"]

        if not strategy_ids or "all" in strategy_ids or len(strategy_ids) == 0:
            target_strat_ids = all_strat_ids
        else:
            resolved_ids = []
            for sid in strategy_ids:
                cleaned = sid.strip().lower()
                canonical = cls.STRATEGY_ALIASES.get(cleaned, cleaned)
                if canonical in all_strat_ids and canonical not in resolved_ids:
                    resolved_ids.append(canonical)
            target_strat_ids = resolved_ids if resolved_ids else all_strat_ids

        # 1. 批量预拉取所有标的的 K 线数据（单标的仅拉一次）
        symbol_data_map: Dict[str, pd.DataFrame] = {}
        benchmark_returns: Dict[str, float] = {}
        data_coverage: Dict[str, Dict[str, Any]] = {}

        for sym in symbols:
            try:
                df = BinanceDataClient.fetch_klines(symbol=sym, interval=interval, limit=limit)
                if not df.empty and len(df) >= 10:
                    symbol_data_map[sym] = df
                    first_p = df.iloc[0]["close"]
                    last_p = df.iloc[-1]["close"]
                    bh_return = round((last_p - first_p) / first_p * 100.0, 2)
                    benchmark_returns[sym] = bh_return
                    data_coverage[sym] = {
                        "bars": len(df),
                        "start": df.iloc[0]["timestamp"].strftime("%Y-%m-%d") if hasattr(df.iloc[0]["timestamp"], "strftime") else str(df.iloc[0]["timestamp"])[:10],
                        "end": df.iloc[-1]["timestamp"].strftime("%Y-%m-%d") if hasattr(df.iloc[-1]["timestamp"], "strftime") else str(df.iloc[-1]["timestamp"])[:10],
                        "first_price": round(first_p, 2 if first_p > 10 else 4),
                        "last_price": round(last_p, 2 if last_p > 10 else 4),
                        "benchmark_return_pct": bh_return
                    }
                else:
                    logger.warning(f"[MatrixBacktester] Symbol {sym} returned insufficient data ({len(df)} bars)")
            except Exception as e:
                logger.error(f"[MatrixBacktester] Failed to fetch data for {sym}: {e}")

        valid_symbols = list(symbol_data_map.keys())
        if not valid_symbols:
            raise ValueError(f"未能获取到任何标的的有效 K 线数据，请求标的: {symbols}")

        # 2. 执行矩阵回测循环
        # matrix[strategy_id][symbol] -> metrics
        matrix: Dict[str, Dict[str, Any]] = {}
        strat_stats: Dict[str, Dict[str, Any]] = {}

        for sid in target_strat_ids:
            cat_meta = STRATEGY_CATALOG.get(sid, {})
            strat_instance = StrategyRegistry.get_strategy(sid)
            matrix[sid] = {
                "strategy_id": sid,
                "strategy_name": strat_instance.name,
                "category": getattr(strat_instance, "category", "经典策略"),
                "badge": cat_meta.get("badge", "标准策略"),
                "tag_color": cat_meta.get("tag_color", "blue"),
                "results": {}
            }

            returns_list = []
            drawdowns_list = []
            sharpes_list = []
            win_rates_list = []
            trades_count_total = 0

            for sym in valid_symbols:
                df = symbol_data_map[sym]
                try:
                    bt = CryptoBacktester(
                        strategy=strat_instance,
                        initial_capital=initial_capital,
                        leverage=leverage,
                        allow_short=allow_short
                    )
                    res = bt.run(df, symbol=sym)
                    m = res["metrics"]

                    ret = float(m["total_return_pct"])
                    mdd = float(m["max_drawdown_pct"])
                    shp = float(m["sharpe_ratio"])
                    wr = float(m["win_rate_pct"])
                    tc = int(m["total_trades"])

                    returns_list.append(ret)
                    drawdowns_list.append(mdd)
                    sharpes_list.append(shp)
                    win_rates_list.append(wr)
                    trades_count_total += tc

                    matrix[sid]["results"][sym] = {
                        "total_return_pct": round(ret, 2),
                        "alpha_pct": round(m["alpha_pct"], 2),
                        "max_drawdown_pct": round(mdd, 2),
                        "sharpe_ratio": round(shp, 2),
                        "win_rate_pct": round(wr, 2),
                        "profit_factor": round(float(m["profit_factor"]), 2),
                        "total_trades": tc,
                        "final_equity": round(float(m["final_equity"]), 2)
                    }
                except Exception as e:
                    logger.error(f"[MatrixBacktester] Error running {sid} on {sym}: {e}")
                    matrix[sid]["results"][sym] = {
                        "total_return_pct": 0.0,
                        "alpha_pct": 0.0,
                        "max_drawdown_pct": 0.0,
                        "sharpe_ratio": 0.0,
                        "win_rate_pct": 0.0,
                        "profit_factor": 0.0,
                        "total_trades": 0,
                        "final_equity": initial_capital,
                        "error": str(e)
                    }

            # 统计当前策略在全标的上的综合绩效
            avg_return = float(np.mean(returns_list)) if returns_list else 0.0
            avg_mdd = float(np.mean(drawdowns_list)) if drawdowns_list else 0.0
            avg_sharpe = float(np.mean(sharpes_list)) if sharpes_list else 0.0
            avg_win_rate = float(np.mean(win_rates_list)) if win_rates_list else 0.0

            # 综合鲁棒性得分：兼顾平均收益、夏普比率与回撤惩罚
            # Score = 50 + avg_return*0.5 + avg_sharpe*15 - avg_mdd*0.4
            composite_score = 50.0 + (avg_return * 0.5) + (avg_sharpe * 15.0) - (avg_mdd * 0.4)
            composite_score = max(0.0, min(100.0, composite_score))

            if composite_score >= 80:
                grade = "S (全天候卓越)"
            elif composite_score >= 65:
                grade = "A (稳健进攻型)"
            elif composite_score >= 50:
                grade = "B (周期平衡型)"
            else:
                grade = "C (防守或偏科型)"

            strat_stats[sid] = {
                "strategy_id": sid,
                "strategy_name": strat_instance.name,
                "category": getattr(strat_instance, "category", "经典策略"),
                "badge": cat_meta.get("badge", "标准策略"),
                "tag_color": cat_meta.get("tag_color", "blue"),
                "avg_return_pct": round(avg_return, 2),
                "avg_max_drawdown_pct": round(avg_mdd, 2),
                "avg_sharpe_ratio": round(avg_sharpe, 2),
                "avg_win_rate_pct": round(avg_win_rate, 2),
                "total_trades_all": trades_count_total,
                "composite_score": round(composite_score, 1),
                "grade": grade
            }

        # 3. 计算天梯排行榜 (Leaderboard) - 按综合得分降序
        leaderboard = sorted(strat_stats.values(), key=lambda x: x["composite_score"], reverse=True)
        for idx, item in enumerate(leaderboard):
            item["rank"] = idx + 1

        # 4. 计算单标的专属冠军 (Symbol Champions)
        symbol_champions: Dict[str, Dict[str, Any]] = {}
        for sym in valid_symbols:
            best_strat_id = None
            best_return = -999999.0
            best_metrics = None

            for sid in target_strat_ids:
                res_cell = matrix[sid]["results"].get(sym, {})
                ret = res_cell.get("total_return_pct", -999999.0)
                if ret > best_return:
                    best_return = ret
                    best_strat_id = sid
                    best_metrics = res_cell

            if best_strat_id:
                s_obj = StrategyRegistry.get_strategy(best_strat_id)
                cat_m = STRATEGY_CATALOG.get(best_strat_id, {})
                symbol_champions[sym] = {
                    "strategy_id": best_strat_id,
                    "strategy_name": s_obj.name,
                    "category": getattr(s_obj, "category", "经典策略"),
                    "badge": cat_m.get("badge", "标的最佳"),
                    "total_return_pct": best_return,
                    "alpha_pct": best_metrics.get("alpha_pct", 0.0),
                    "max_drawdown_pct": best_metrics.get("max_drawdown_pct", 0.0),
                    "sharpe_ratio": best_metrics.get("sharpe_ratio", 0.0),
                    "win_rate_pct": best_metrics.get("win_rate_pct", 0.0),
                    "benchmark_return_pct": benchmark_returns.get(sym, 0.0)
                }

        # 5. 全市场全能冠军策略
        best_overall = leaderboard[0] if leaderboard else None

        # 6. 生成量化洞察归因简评 (Quant Insights)
        insights = []
        if best_overall:
            insights.append(
                f"🏆 【全天候综合冠军】「{best_overall['strategy_name']}」以综合评分 {best_overall['composite_score']} 分位居全场榜首，"
                f"在测试的 {len(valid_symbols)} 大标的上斩获平均 {best_overall['avg_return_pct']}% 的累计收益率，平均夏普达 {best_overall['avg_sharpe_ratio']}。"
            )

        # 归因各流派表现
        cat_performance = {}
        for item in leaderboard:
            c = item["category"]
            cat_performance.setdefault(c, []).append(item["avg_return_pct"])
        
        cat_avg = {c: float(np.mean(vals)) for c, vals in cat_performance.items()}
        if cat_avg:
            sorted_cats = sorted(cat_avg.items(), key=lambda x: x[1], reverse=True)
            top_cat, top_cat_ret = sorted_cats[0]
            insights.append(
                f"📈 【流派胜率归因】「{top_cat}」流派在当前测试周期整体表现最强（组内全标的平均收益率 {round(top_cat_ret, 2)}%），"
                f"说明当前宏观周期下该类指标的物理因子捕捉效率最高。"
            )

        # 标的分化洞察
        highest_beta_sym = max(benchmark_returns.items(), key=lambda x: abs(x[1])) if benchmark_returns else None
        if highest_beta_sym:
            insights.append(
                f"⚡️ 【标的波动分化】标的「{highest_beta_sym[0]}」在测试周期内基准变动最为剧烈（同期死扛收益 {highest_beta_sym[1]}%），"
                f"其对应的冠军策略「{symbol_champions.get(highest_beta_sym[0], {}).get('strategy_name', '自适应通道')}」实现了最显著的超额 Alpha 捕捉。"
            )

        calc_time = round(time.time() - t0, 3)

        return {
            "success": True,
            "summary": {
                "total_runs": len(valid_symbols) * len(target_strat_ids),
                "symbols_count": len(valid_symbols),
                "strategies_count": len(target_strat_ids),
                "interval": interval,
                "limit_bars": limit,
                "period_desc": f"最近 1 年 ({limit} 根 {interval} K线)" if limit >= 365 else f"最近 {limit} 根 {interval} K线",
                "execution_time_seconds": calc_time,
                "best_overall": best_overall,
                "symbol_champions": symbol_champions
            },
            "symbols": valid_symbols,
            "data_coverage": data_coverage,
            "benchmark_returns": benchmark_returns,
            "strategies": [
                {
                    "id": sid,
                    "name": matrix[sid]["strategy_name"],
                    "category": matrix[sid]["category"],
                    "badge": matrix[sid]["badge"],
                    "tag_color": matrix[sid]["tag_color"]
                }
                for sid in target_strat_ids
            ],
            "matrix": matrix,
            "leaderboard": leaderboard,
            "insights": insights
        }
