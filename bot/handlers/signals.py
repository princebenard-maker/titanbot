"""
signals.py - TITAN V1
Signal commands - retrieve latest analysis from scanner.
Scheduler does the analysis. Commands retrieve results.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
from data.market_fetcher import fetch_ohlcv, is_supported, SUPPORTED_PAIRS
from engines.alpha_trendflow import generate_signal
from engines.regime_classifier import classify_regime
from engines.confidence_engine import calculate_score
from engines.scanner import get_scanner, ScanStatus

logger = logging.getLogger(__name__)

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Retrieve latest signal decision for a pair.
    The scanner already analyzed this pair. We just return the result.
    """
    if not context.args:
        pairs = ", ".join([p.replace('/','') for p in SUPPORTED_PAIRS])
        await update.message.reply_text(
            f"Usage: /signal BTCUSDT\nSupported: {pairs}")
        return
    
    symbol_input = context.args[0].upper()
    if not is_supported(symbol_input):
        await update.message.reply_text(
            f"❌ {symbol_input} not supported.\nTry: BTCUSDT, ETHUSDT, SOLUSDT")
        return
    
    # Get cached result from scanner (scheduler already analyzed this)
    scanner = get_scanner()
    cached = scanner.get_cached_result(symbol_input)
    
    if cached:
        # Return cached result
        status_emoji = {
            ScanStatus.TRADE: "🟢",
            ScanStatus.REJECT: "⚪",
            ScanStatus.WAIT: "🟡",
            ScanStatus.LOW_VOLUME: "⚠️",
            ScanStatus.BAD_REGIME: "⚠️",
            ScanStatus.LOW_CONFIDENCE: "⚠️",
        }
        emoji = status_emoji.get(cached.status, "⚪")
        
        # Decision based on status
        if cached.status == ScanStatus.TRADE:
            decision = "LONG"
            decision_emoji = "🟢"
        elif cached.status == ScanStatus.REJECT:
            decision = "WATCH"
            decision_emoji = "⚪"
        else:
            decision = "WAIT"
            decision_emoji = "🟡"
        
        # Get next scan time
        from datetime import datetime
        last_scan = scanner._last_scan.get(symbol_input)
        if last_scan:
            minutes_since = (datetime.utcnow() - last_scan).total_seconds() / 60
            next_scan = max(0, 15 - int(minutes_since))
        else:
            next_scan = 15
        
        msg = f"📊 Current Decision — {symbol_input}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"Decision: {decision_emoji} {decision}\n"
        msg += f"Confidence: {cached.score}/40\n"
        msg += f"Regime: {cached.regime}\n"
        msg += f"Volume: {cached.volume_ratio:.2f}x avg\n"
        msg += f"ATR: {cached.atr_pct:.2f}%\n"
        
        if cached.confidence_breakdown:
            msg += "━━━━━━━━━━━━━━━━━━━━\n"
            msg += "Score Breakdown:\n"
            for factor, score in cached.confidence_breakdown.items():
                bar = "█" * (score // 2) + "░" * (10 - score // 2)
                msg += f"  {factor}: {bar} ({score})\n"
        
        if cached.rejection_reasons:
            msg += "━━━━━━━━━━━━━━━━━━━━\n"
            msg += "Reason:\n"
            for reason in cached.rejection_reasons[:3]:
                msg += f"  • {reason}\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"Next Scheduled Scan: {next_scan} min\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "_Analysis performed by autonomous scanner_"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        # No cached result - do fresh analysis (fallback)
        await update.message.reply_text(f"🔍 No cached analysis for {symbol_input}.\nPerforming fresh scan...")
        await _perform_fresh_analysis(update, symbol_input)


async def _perform_fresh_analysis(update: Update, symbol_input: str):
    """
    Fallback: Perform fresh analysis if no cached result exists.
    This should rarely happen once scanner is running.
    """
    symbol = symbol_input.replace('USDT', '/USDT')
    try:
        df_4h = await fetch_ohlcv(symbol, '4h', 200)
        df_1h = await fetch_ohlcv(symbol, '1h', 200)
        df_15m = await fetch_ohlcv(symbol, '15m', 200)
        result = generate_signal(df_4h, df_1h, df_15m)

        from core.decision_journal import save_signal
        if result.get('signal') != 'WAIT':
            try:
                await save_signal(
                    symbol=symbol_input,
                    signal=result.get('signal','WAIT'),
                    score=result.get('score', 0),
                    regime=result.get('regime','UNKNOWN'),
                    score_breakdown=result.get('score_breakdown', {}),
                    reasons=result.get('reasons', {}),
                    setup_type=result.get('setup_type', 'N/A')
                )
            except Exception as e:
                logger.warning(f"Could not save signal: {e}")
        
        signal = result.get('signal', 'WAIT')
        score = result.get('score', 0)
        regime = result.get('regime', 'UNKNOWN')
        reason = result.get('reason', '')
        setup_type = result.get('setup_type', 'N/A')
        emoji = "🟢" if signal=="LONG" else "🔴" if signal=="SHORT" else "⚪"
        
        setup_display = setup_type.replace('_', ' ') if setup_type else 'N/A'
        
        await update.message.reply_text(
            f"📊 Fresh Analysis — {symbol_input}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Signal: {emoji} {signal}\n"
            f"Score: {score}/40\n"
            f"Regime: {regime}\n"
            f"Setup: {setup_display}\n"
            f"Reason: {reason}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"_Note: Scanner cache miss - scan will update on next cycle_")
    except Exception as e:
        logger.error(f"Signal failed: {e}")
        await update.message.reply_text("❌ Analysis failed. Try again.")

async def regime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /regime BTCUSDT")
        return
    symbol_input = context.args[0].upper()
    symbol = symbol_input.replace('USDT', '/USDT')
    await update.message.reply_text(f"🔍 Checking regime for {symbol_input}...")
    try:
        df = await fetch_ohlcv(symbol, '4h', 200)
        regime = classify_regime(df)
        await update.message.reply_text(
            f"Market Regime — {symbol_input}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Regime: {regime.get('regime','UNKNOWN')}\n"
            f"Confidence: {regime.get('confidence',0)}%\n"
            f"ATR%: {regime.get('atr_pct',0)}\n"
            f"Note: {regime.get('note','')}\n"
            f"━━━━━━━━━━━━━━━━━━━━")
    except Exception as e:
        await update.message.reply_text("❌ Regime check failed.")

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /score BTCUSDT")
        return
    symbol_input = context.args[0].upper()
    symbol = symbol_input.replace('USDT', '/USDT')
    await update.message.reply_text(f"🔍 Calculating score for {symbol_input}...")
    try:
        df = await fetch_ohlcv(symbol, '4h', 200)
        regime = classify_regime(df)
        score_data = calculate_score(df, regime)
        msg = f"Titan Score — {symbol_input}\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"Total: {score_data['total']}/40\n"
        msg += f"Verdict: {score_data['verdict']}\n\n"
        msg += "Breakdown:\n"
        for k, v in score_data['breakdown'].items():
            msg += f"• {k}: {v}\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("❌ Score calculation failed.")

def register_signals(application: Application):
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("regime", regime_command))
    application.add_handler(CommandHandler("score", score_command))
