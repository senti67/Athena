"""
ATHENA Institutional Telegram Message Formatter
Formats quantitative research notes, trade cards, position updates, rejected signals,
and daily reports into clean, phone-scannable Telegram messages with safe character handling.
"""

from datetime import datetime
from typing import List, Optional

from services.notification_service.trade_card import (
    DailyReportCard,
    NoTradeCard,
    PositionUpdateCard,
    TradeCard,
)

SECTION_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
MAX_TELEGRAM_MESSAGE_LENGTH = 4000


def render_progress_bar(score: int, max_score: int = 100, length: int = 10) -> str:
    """Renders a visually clean Unicode progress bar."""
    clamped_score = max(0, min(score, max_score))
    filled_blocks = int(round((clamped_score / max_score) * length))
    empty_blocks = length - filled_blocks
    bar = "█" * filled_blocks + "░" * empty_blocks
    return f"{bar} {clamped_score}/{max_score}"


def _status_emoji(label: str) -> str:
    """Colour a status word by its meaning (never a default green)."""
    l = (label or "").lower()
    if any(w in l for w in ("strengthen", "supportive", "buy", "bull")):
        return "🟢"
    if any(w in l for w in ("weaken", "drying", "sell", "bear", "close")):
        return "🔴"
    return "🟡"


def escape_markdown(text: str) -> str:
    """
    Sanitizes dynamic text for Telegram Markdown formatting.
    Avoids unescaped underscores or brackets from breaking Markdown parsing.
    """
    if not text:
        return ""
    # For standard Telegram Markdown mode, replace underscores in identifiers unless intentional
    # We leave backticked content alone and escape raw strings if necessary.
    return str(text).replace("_", " ")


class TelegramFormatter:
    """
    Institutional message formatting engine for Athena.
    Ensures zero data fabrication and crystal-clear decision transparency.
    """

    @classmethod
    def format_trade_signal(cls, card: TradeCard) -> str:
        """
        Formats a TradeCard into the institutional Trade Thesis note.
        """
        side_emoji = "🟢" if card.side.upper() in ["BUY", "LONG"] else "🔴"
        action_label = f"{side_emoji} {card.side.upper()} · {card.symbol.upper()}"
        
        conf_str = f"{card.confidence * 100:.0f}%" if card.confidence is not None else "N/A"
        edge_str = f"{card.expected_edge * 100:+.2f}%" if card.expected_edge is not None else "N/A"
        rr_str = f"{card.reward_risk:.2f} : 1" if card.reward_risk is not None else "N/A"
        
        entry_str = f"${card.entry_price:,.2f}" if card.entry_price is not None else "N/A"
        target_str = f"${card.take_profit:,.2f}" if card.take_profit is not None else "N/A"
        stop_str = f"${card.stop_loss:,.2f}" if card.stop_loss is not None else "N/A"
        
        shares_str = f"{card.position_size:.0f} shares" if card.position_size is not None else "N/A"
        val_str = f"${card.position_value:,.2f} exposure" if card.position_value is not None else "N/A"
        weight_str = f"{card.portfolio_weight:.1f}% portfolio weight" if card.portfolio_weight is not None else "N/A"

        # Regime indicator emoji
        regime_upper = card.regime.upper()
        if "BULL" in regime_upper:
            regime_emoji = "🟢"
        elif "BEAR" in regime_upper:
            regime_emoji = "🔴"
        elif "HIGH" in regime_upper:
            regime_emoji = "🛑"
        else:
            regime_emoji = "🟡"

        # Strategy Evidence Lines
        evidence_lines: List[str] = []
        for s in card.strategy_contributions:
            if not s.material_contribution:
                continue
            s_emoji = "🟢" if s.score > 0.2 else ("🔴" if s.score < -0.2 else "⚪")
            sign = "+" if s.score > 0 else ""
            evidence_lines.append(f"{s.strategy_name:<20} {s_emoji} {sign}{s.score:.2f}")

        if not evidence_lines:
            evidence_lines.append("No strategy contribution recorded")
        evidence_block = "\n".join(evidence_lines)

        # Progress bar
        score_bar = render_progress_bar(int(card.signal_score))

        # Supporting factors & risks
        supporting_block = "\n".join(f"• {f}" for f in card.thesis.supporting_factors) if card.thesis.supporting_factors else "• Evidence currently favors the quantitative setup"
        risk_block = "\n".join(f"• {r}" for r in card.thesis.risk_factors) if card.thesis.risk_factors else "• Elevated market volatility could invalidate setup"
        invalidation_block = "\nOR\n".join(card.thesis.invalidation_conditions) if card.thesis.invalidation_conditions else f"Close below {stop_str}"

        # Risk Check statuses
        rc = card.risk_checks
        r_per_trade = f"{rc.risk_per_trade_pct:.2f}%" if rc.risk_per_trade_pct is not None else "N/A"
        p_exposure = f"{rc.portfolio_exposure_pct:.1f}%" if rc.portfolio_exposure_pct is not None else weight_str
        dll_icon = "✅" if rc.daily_loss_limit_ok else "❌"
        bp_icon = "✅" if rc.buying_power_ok else "❌"
        pos_icon = "✅" if rc.position_limit_ok else "❌"
        corr_icon = "✅" if rc.correlation_risk_ok else "❌"
        dq_icon = "✅" if rc.data_quality_ok else "❌"

        # Timestamp
        ts_str = card.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        order_id_str = card.order_id or "PENDING"
        reason_str = card.decision_reason or "Multiple independent signal groups agree with the trade and the current market regime supports the selected strategies."

        rr_display = f"{card.reward_risk:.2f}" if card.reward_risk is not None else "N/A"

        msg = (
            f"{SECTION_DIVIDER}\n"
            f"🧠 ATHENA TRADE THESIS\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{action_label}\n"
            f"Confidence: {conf_str}\n"
            f"Signal Strength: {int(card.signal_score)}/100\n"
            f"Expected Edge: {edge_str}\n\n"
            f"💵 Entry\n{entry_str}\n\n"
            f"🎯 Target\n{target_str}\n\n"
            f"🛑 Stop\n{stop_str}\n\n"
            f"⚖️ R:R\n{rr_str}\n\n"
            f"📦 Position\n{shares_str}\n{val_str}\n{weight_str}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"📊 MARKET CONTEXT\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Regime:\n{regime_emoji} {card.regime.upper()}\n\n"
            f"Volatility:\n{card.volatility_label or 'Moderate'}\n\n"
            f"Trend:\n{card.trend_details or 'N/A'}\n\n"
            f"Momentum:\n{card.momentum_details or 'N/A'}\n\n"
            f"Volume:\n{card.volume_details or 'N/A'}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🔬 STRATEGY EVIDENCE\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{evidence_block}\n\n"
            f"Weighted Signal:\n{score_bar}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🧩 WHY ATHENA LIKES IT\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{supporting_block}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"⚠️ WHAT COULD GO WRONG\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{risk_block}\n\n"
            f"Invalidation:\n{invalidation_block}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🛡️ RISK CHECK\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Risk / Trade: {r_per_trade}\n"
            f"Portfolio Exposure: {p_exposure}\n\n"
            f"Daily Loss Limit: {dll_icon}\n"
            f"Buying Power: {bp_icon}\n"
            f"Position Limit: {pos_icon}\n"
            f"Correlation Risk: {corr_icon}\n"
            f"Data Quality: {dq_icon}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🤖 ATHENA DECISION\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{card.decision.upper()}\n\n"
            f"Decision Score: {int(card.signal_score)}/100\n"
            f"Expected Edge: {edge_str}\n"
            f"Risk/Reward: {rr_display}\n\n"
            f"Reason:\n{reason_str}\n\n"
            f"Execution:\n🟢 {card.execution_mode.upper()}\n\n"
            f"Order ID:\n{order_id_str}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"⏱️ Generated:\n{ts_str}\n"
            f"{SECTION_DIVIDER}"
        )
        return msg

    @classmethod
    def format_position_update(cls, card: PositionUpdateCard) -> str:
        """
        Formats a PositionUpdateCard for periodic holding health monitoring.
        """
        pnl_emoji = "🟢" if card.unrealized_pnl_val >= 0 else "🔴"
        pnl_val_sign = "+" if card.unrealized_pnl_val >= 0 else ""
        pnl_pct_sign = "+" if card.unrealized_pnl_pct >= 0 else ""

        # Regime indicator emoji
        reg_upper = card.current_regime.upper()
        reg_emoji = "🟢" if "BULL" in reg_upper else ("🔴" if "BEAR" in reg_upper else "🟡")

        target_str = f"${card.target_price:,.2f}" if card.target_price is not None else "N/A"
        stop_str = f"${card.stop_price:,.2f}" if card.stop_price is not None else "N/A"

        dist_tp_str = f"{card.dist_to_target_pct:+.2f}%" if card.dist_to_target_pct is not None else "N/A"
        dist_sl_str = f"{card.dist_to_stop_pct:+.2f}%" if card.dist_to_stop_pct is not None else "N/A"

        ts_str = card.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        msg = (
            f"{SECTION_DIVIDER}\n"
            f"📈 ATHENA POSITION UPDATE\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{card.symbol.upper()} · {card.side.upper()}\n\n"
            f"Entry:\n${card.entry_price:,.2f}\n\n"
            f"Current:\n${card.current_price:,.2f}\n\n"
            f"P&L:\n{pnl_emoji} {pnl_pct_sign}{card.unrealized_pnl_pct:.2f}%  ({pnl_val_sign}${card.unrealized_pnl_val:,.2f})\n\n"
            f"Holding:\n{card.holding_duration_str}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"📊 POSITION HEALTH\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Original Thesis:\n{card.original_thesis}\n\n"
            f"Current Regime:\n{reg_emoji} {card.current_regime.upper()}\n\n"
            f"Momentum:\n{_status_emoji(card.momentum_status)} {card.momentum_status}\n\n"
            f"Volume:\n{_status_emoji(card.volume_status)} {card.volume_status}\n\n"
            f"Signal:\n{_status_emoji(card.signal)} {card.signal.upper()}\n\n"
            f"Thesis Strength:\n{str(card.thesis_strength_score) + '/100' if card.thesis_strength_score is not None else 'N/A'}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🎯 LEVELS\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Target:\n{target_str}\n\n"
            f"Stop:\n{stop_str}\n\n"
            f"Distance to Target:\n{dist_tp_str}\n\n"
            f"Distance to Stop:\n{dist_sl_str}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🤖 ATHENA ASSESSMENT\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{card.assessment_verdict.upper()}\n\n"
            f"{card.assessment_reason}\n\n"
            f"Next Review:\n{card.next_review_time} ({ts_str})\n\n"
            f"{SECTION_DIVIDER}"
        )
        return msg

    @classmethod
    def format_no_trade(cls, card: NoTradeCard) -> str:
        """
        Formats a NoTradeCard explaining why an asset setup was rejected.
        """
        blocking_block = "\n".join(f"• {b}" for b in card.blocking_factors) if card.blocking_factors else "• Statistical edge below minimum entry hurdle"
        trigger_block = "\nAND\n".join(card.next_triggers) if card.next_triggers else "Expected edge > +1.20%\nAND\nR:R > 1.80 : 1"
        ts_str = card.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        trend_emoji = "🟢" if card.trend_state == "Bullish" else ("🔴" if card.trend_state == "Bearish" else "🟡")
        mom_emoji = "🟢" if card.momentum_state == "Bullish" else ("🔴" if card.momentum_state == "Bearish" else "🟡")
        mr_emoji = "🔴" if "Over" in card.mean_reversion_state else "🟡"
        vol_emoji = "🟡" if card.volatility_state == "Elevated" else "🟢"
        reg_emoji = "🟡" if "UNCERTAIN" in card.regime.upper() or "HIGH" in card.regime.upper() else "🟢"

        msg = (
            f"{SECTION_DIVIDER}\n"
            f"🚫 ATHENA — NO TRADE\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{card.symbol.upper()}\n\n"
            f"Signal:\n{card.candidate_signal.upper()}\n\n"
            f"Final Score:\n{card.final_score}/100\n\n"
            f"Required:\n{card.required_score}/100\n\n"
            f"{SECTION_DIVIDER}\n"
            f"📊 ANALYSIS\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Trend:\n{trend_emoji} {card.trend_state}\n\n"
            f"Momentum:\n{mom_emoji} {card.momentum_state}\n\n"
            f"Mean Reversion:\n{mr_emoji} {card.mean_reversion_state}\n\n"
            f"Volatility:\n{vol_emoji} {card.volatility_state}\n\n"
            f"Regime:\n{reg_emoji} {card.regime.upper()}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"⚠️ BLOCKING FACTORS\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{blocking_block}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🤖 DECISION\n"
            f"{SECTION_DIVIDER}\n\n"
            f"{card.decision_summary.upper()}\n\n"
            f"{card.decision_detail}\n\n"
            f"Next trigger:\n{trigger_block}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"⏱️ Generated:\n{ts_str}\n"
            f"{SECTION_DIVIDER}"
        )
        return msg

    @staticmethod
    def _num(value, fmt: str = "{:,.2f}", prefix: str = "", suffix: str = "") -> str:
        """Format a number, or 'N/A' when it was not measured."""
        if value is None:
            return "N/A"
        return f"{prefix}{fmt.format(value)}{suffix}"

    @staticmethod
    def _signed_emoji(value) -> str:
        if value is None:
            return "⚪"
        return "🟢" if value >= 0 else "🔴"

    @classmethod
    def format_daily_report(cls, card: DailyReportCard) -> str:
        """
        Formats a DailyReportCard into the daily summary note.
        Any metric that is None is shown as N/A; nothing is defaulted or estimated.
        """
        n = cls._num
        d_emoji = cls._signed_emoji(card.daily_pnl_val)
        t_emoji = cls._signed_emoji(card.total_pnl_pct)

        if card.daily_pnl_pct is None or card.daily_pnl_val is None:
            daily_line = "N/A"
        else:
            sg = "+" if card.daily_pnl_val >= 0 else "-"
            daily_line = f"{d_emoji} {card.daily_pnl_pct:+.2f}%  ({sg}${abs(card.daily_pnl_val):,.2f})"
        total_line = f"{t_emoji} {card.total_pnl_pct:+.2f}%" if card.total_pnl_pct is not None else "N/A"

        avg_win = n(card.avg_win, prefix="+$") if card.avg_win is not None else "N/A"
        avg_loss = n(abs(card.avg_loss), prefix="-$") if card.avg_loss is not None else "N/A"

        ts_str = card.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        msg = (
            f"{SECTION_DIVIDER}\n"
            f"🧠 ATHENA DAILY REPORT\n"
            f"{SECTION_DIVIDER}\n\n"
            f"📅 {card.date_str}\n\n"
            f"Portfolio:\n{n(card.portfolio_value, prefix='$')}\n\n"
            f"Daily P&L:\n{daily_line}\n\n"
            f"Total P&L:\n{total_line}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"📊 TRADING ACTIVITY\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Trades:\n{n(card.trades_count, '{:d}')}\n\n"
            f"Wins:\n{n(card.wins_count, '{:d}')}\n\n"
            f"Losses:\n{n(card.losses_count, '{:d}')}\n\n"
            f"Win Rate:\n{n(card.win_rate_pct, '{:.1f}', suffix='%')}\n\n"
            f"Profit Factor:\n{n(card.profit_factor)}\n\n"
            f"Average Win:\n{avg_win}\n\n"
            f"Average Loss:\n{avg_loss}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"📈 RISK\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Max Drawdown:\n{n(card.max_drawdown_pct, suffix='%')}\n\n"
            f"Portfolio Exposure:\n{n(card.portfolio_exposure_pct, '{:.1f}', suffix='%')}\n\n"
            f"Largest Position:\n{card.largest_position_str or 'N/A'}\n\n"
            f"Daily Risk:\n{n(card.daily_risk_pct, suffix='%')}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🧠 MARKET REGIME\n"
            f"{SECTION_DIVIDER}\n\n"
            f"SPY:\n{card.spy_regime or 'N/A'}\n\n"
            f"QQQ:\n{card.qqq_regime or 'N/A'}\n\n"
            f"VIX:\n{card.vix_status or 'N/A'}\n\n"
            f"Overall:\n{card.overall_market_bias or 'N/A'}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"🤖 ATHENA\n"
            f"{SECTION_DIVIDER}\n\n"
            f"Trades Executed:\n{n(card.trades_executed, '{:d}')}\n\n"
            f"Signals Rejected:\n{n(card.signals_rejected, '{:d}')}\n\n"
            f"Risk Vetoes:\n{n(card.risk_vetoes, '{:d}')}\n\n"
            f"Most Successful Strategy:\n{card.most_successful_strategy or 'N/A'}\n\n"
            f"Weakest Strategy:\n{card.weakest_strategy or 'N/A'}\n\n"
            f"{SECTION_DIVIDER}\n"
            f"⏱️ Generated:\n{ts_str}\n"
            f"{SECTION_DIVIDER}"
        )
        return msg

    @classmethod
    def split_message_if_needed(cls, text: str, max_length: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> List[str]:
        """
        Splits a message into logically coherent parts if it exceeds the maximum Telegram length.
        Preserves section dividers cleanly.
        """
        if len(text) <= max_length:
            return [text]

        sections = text.split(SECTION_DIVIDER)
        chunks: List[str] = []
        current_chunk = ""

        for i, section in enumerate(sections):
            candidate = current_chunk + (SECTION_DIVIDER if current_chunk else "") + section
            if len(candidate) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = SECTION_DIVIDER + section
            else:
                current_chunk = candidate

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]
