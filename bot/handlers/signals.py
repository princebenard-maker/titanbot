"""
signals.py - TITAN Wave 2A
Signal commands. Read-only. No trading.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
from data.market_fetcher import fetch_ohlcv, is_supported, SUPPORTED_PAIRS
from engines.alpha_trendflow import generate_signal
from engines.regime_classifier import classify_regime
from engines.confidence_engine import calculate_score

logger = logging.getLogger(__name__)

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    symbol = symbol_input.replace('USDT', '/USDT')
    await update.message.reply_text(f"🔍 Analyzing {symbol_input}...")
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
                    score_breakdown=result.get(
                        'score_breakdown', {}),
                    reasons=result.get('reasons', {})
                )
            except Exception as e:
                logger.warning(f"Could not save signal: {e}")
        signal = result.get('signal', 'WAIT')
        score = result.get('score', 0)
        regime = result.get('regime', 'UNKNOWN')
        reason = result.get('reason', '')
        emoji = "🟢" if signal=="LONG" else "🔴" if signal=="SHORT" else "⚪"
        await update.message.reply_text(
            f"Titan Signal — {symbol_input}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Signal: {emoji} {signal}\n"
            f"Score: {score}/40\n"
            f"Regime: {regime}\n"
            f"Reason: {reason}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Paper mode only. Not financial advice.")
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
