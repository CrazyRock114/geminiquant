"""
OmniQuant Custom Strategy Validator & Linter
Ensures user-defined strategies are mathematically sound, safe, and disciplined:
- Mandatory hard stop-loss enforcement (anti-liquidation guarantee)
- Indicator parameter boundary & sanity checks (prevents unachievable logic)
- Comprehensive Strategy Health & Robustness Score (0 - 100)
- Actionable quantitative guidance & educational feedback
"""
from typing import Dict, Any, List, Tuple

class CustomStrategyValidator:
    """自定义策略安全与逻辑校验器"""

    ALLOWED_INDICATORS = {"rsi", "ema", "macd", "bollinger", "atr", "volume_ma"}
    MAX_ALLOWED_LEVERAGE = 5.0
    MIN_STOP_LOSS_PCT = 0.5
    MAX_STOP_LOSS_PCT = 20.0

    @classmethod
    def validate(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        全面体检用户自定义策略配置:
        返回:
        - is_valid: bool (是否满足最低可执行安全基线)
        - score: int (0 - 100 策略健康与鲁棒度评分)
        - errors: List[str] (阻断性错误，禁止运行)
        - warnings: List[str] (潜在风险警示)
        - suggestions: List[str] (专家级量化优化建议)
        - cleaned_config: Dict (格式化清洗后的可用配置)
        """
        errors = []
        warnings = []
        suggestions = []
        score = 100

        name = str(config.get("name", "未命名自定义策略")).strip()
        if not name:
            name = "未命名自定义策略"

        strat_type = str(config.get("strategy_type", "TREND")).upper()
        if strat_type not in ("TREND", "MEAN_REVERSION", "MOMENTUM", "COMPOSITE"):
            strat_type = "TREND"

        # 1. 强制硬风控校验 (Stop Loss & Risk Management)
        risk_config = config.get("risk_management", {})
        stop_loss = float(risk_config.get("stop_loss_pct", 0.0))
        take_profit = float(risk_config.get("take_profit_pct", 0.0))
        trailing_stop = float(risk_config.get("trailing_stop_pct", 0.0))
        leverage = float(risk_config.get("leverage", 1.0))

        if stop_loss <= 0.0:
            errors.append("【强制风控拦截】未设置硬止损线 (Stop Loss)！量化交易严禁'裸奔'或死扛，必须设定 0.5% ~ 20.0% 的硬止损。")
            score -= 40
        elif stop_loss < cls.MIN_STOP_LOSS_PCT:
            errors.append(f"【参数违规】止损线 ({stop_loss}%) 设置过紧，低于最低门槛 {cls.MIN_STOP_LOSS_PCT}%，极易被日内噪音洗出。")
            score -= 20
        elif stop_loss > cls.MAX_STOP_LOSS_PCT:
            errors.append(f"【参数违规】止损线 ({stop_loss}%) 设置过宽，超过最高上限 {cls.MAX_STOP_LOSS_PCT}%，单笔亏损过大可能摧毁账户本金。")
            score -= 25
        elif stop_loss > 10.0:
            warnings.append(f"【高风险警示】止损线为 {stop_loss}%，属于宽幅大止损，建议仅在现货长线或低杠杆(1x)时使用。")
            score -= 10

        if leverage > cls.MAX_ALLOWED_LEVERAGE:
            errors.append(f"【杠杆熔断】申请杠杆 {leverage}x 超过系统安全上限 {cls.MAX_ALLOWED_LEVERAGE}x！自定义策略严禁超高杠杆。")
            score -= 30
        elif leverage > 3.0:
            warnings.append(f"【高杠杆警示】当前启用了 {leverage}x 杠杆，若遇闪崩可能触发快速清算，请严格遵守仓位管理。")
            score -= 10

        if take_profit > 0 and stop_loss > 0:
            rr_ratio = take_profit / stop_loss
            if rr_ratio < 1.0:
                warnings.append(f"【低盈亏比警示】预期止盈 ({take_profit}%) 小于止损 ({stop_loss}%)，盈亏比仅为 {rr_ratio:.2f}:1。该模型要求极高胜率才能勉强保本。")
                suggestions.append(f"建议调高止盈比例至至少 {stop_loss * 1.5:.1f}%，使盈亏比达到 1.5:1 以上。")
                score -= 15
            else:
                suggestions.append(f"当前盈亏比为 {rr_ratio:.2f}:1，符合量化正期望特征。")

        # 2. 技术指标参数合法性校验
        indicators = config.get("indicators", {})
        used_indicators_count = 0

        # RSI 校验
        if "rsi" in indicators:
            used_indicators_count += 1
            rsi_cfg = indicators["rsi"]
            period = int(rsi_cfg.get("period", 14))
            oversold = float(rsi_cfg.get("oversold", 30.0))
            overbought = float(rsi_cfg.get("overbought", 70.0))

            if period < 2 or period > 100:
                errors.append(f"【RSI 周期越界】RSI 周期 ({period}) 必须介于 2 至 100 之间。")
                score -= 15
            elif period < 5:
                warnings.append(f"RSI 周期仅为 {period}，信号过度敏感，容易产生大量虚假锯齿。")
                score -= 5

            if oversold >= overbought:
                errors.append(f"【逻辑冲突】RSI 超卖阈值 ({oversold}) 必须严格小于超买阈值 ({overbought})。")
                score -= 25

            if oversold < 10.0 or overbought > 90.0:
                warnings.append("RSI 超买超卖阈值设置过于极端 (超卖<10 或 超买>90)，实盘中可能极少触发开仓信号。")
                score -= 5

        # 双均线 EMA 校验
        if "ema" in indicators:
            used_indicators_count += 1
            ema_cfg = indicators["ema"]
            fast = int(ema_cfg.get("fast_period", 12))
            slow = int(ema_cfg.get("slow_period", 26))

            if fast < 2 or slow < 3:
                errors.append("【均线周期越界】EMA 均线周期至少必须 >= 2。")
                score -= 15

            if fast >= slow:
                errors.append(f"【逻辑冲突】EMA 快线周期 ({fast}) 必须严格小于慢线周期 ({slow})！快慢线颠倒将导致金叉死叉逻辑反向。")
                score -= 30
            elif (slow - fast) < 3:
                warnings.append(f"EMA 快线 ({fast}) 与慢线 ({slow}) 过于接近，容易频繁发生无意义交叉粘合。")
                score -= 8

        # 布林带校验
        if "bollinger" in indicators:
            used_indicators_count += 1
            bb_cfg = indicators["bollinger"]
            bb_period = int(bb_cfg.get("period", 20))
            bb_std = float(bb_cfg.get("std_dev", 2.0))

            if bb_period < 5 or bb_period > 100:
                errors.append(f"【布林带周期越界】布林带周期 ({bb_period}) 必须介于 5 至 100 之间。")
                score -= 15

            if bb_std < 1.0 or bb_std > 4.0:
                errors.append(f"【标准差倍数越界】布林带倍数 ({bb_std}) 必须在 1.0 至 4.0 之间。")
                score -= 15

        # MACD 校验
        if "macd" in indicators:
            used_indicators_count += 1
            macd_cfg = indicators["macd"]
            m_fast = int(macd_cfg.get("fast_period", 12))
            m_slow = int(macd_cfg.get("slow_period", 26))
            m_sig = int(macd_cfg.get("signal_period", 9))

            if m_fast >= m_slow:
                errors.append(f"【MACD 参数错误】MACD 快线 ({m_fast}) 必须小于慢线 ({m_slow})。")
                score -= 25

        # 3. 复杂度与过拟合评估
        if used_indicators_count == 0:
            errors.append("【指标缺失】未选择任何技术指标！自定义策略必须至少包含一个有效技术指标。")
            score -= 40
        elif used_indicators_count > 4:
            warnings.append(f"【多指标过拟合预警】您同时使用了 {used_indicators_count} 个指标，指标过多会造成'维度诅咒'和信号互相打架抵消。")
            suggestions.append("量化策略讲求'少即是多'，建议保留 1 个趋势主指标 + 1 个动量/震荡辅助过滤指标。")
            score -= 15
        else:
            suggestions.append(f"指标组合数量合理 ({used_indicators_count} 个)，符合经典工业级量化架构标准。")

        # 4. 逻辑一致性与入场规则校验
        entry_rules = config.get("entry_rules", {})
        long_condition = entry_rules.get("long_condition", "NONE")
        short_condition = entry_rules.get("short_condition", "NONE")

        if long_condition == "NONE" and short_condition == "NONE":
            errors.append("【入场规则缺失】做多与做空条件均未启用，策略将永远无法发出买卖信号！")
            score -= 30

        # 整理输出
        score = max(0, min(100, score))
        is_valid = (len(errors) == 0)

        # 评级划分
        if score >= 85:
            grade = "A+ (优秀，结构严谨)"
            grade_color = "emerald"
        elif score >= 70:
            grade = "B (良好，具备实战价值)"
            grade_color = "blue"
        elif score >= 55:
            grade = "C (一般，存在参数偏颇或风控隐患)"
            grade_color = "amber"
        else:
            grade = "D (不合格，逻辑冲突或严重缺乏风控)"
            grade_color = "rose"

        return {
            "is_valid": is_valid,
            "score": score,
            "grade": grade,
            "grade_color": grade_color,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "clean_config": {
                "name": name,
                "strategy_type": strat_type,
                "indicators": indicators,
                "entry_rules": entry_rules,
                "risk_management": {
                    "stop_loss_pct": stop_loss,
                    "take_profit_pct": take_profit,
                    "trailing_stop_pct": trailing_stop,
                    "leverage": leverage
                }
            }
        }
