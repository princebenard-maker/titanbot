"""
signals.py - TITAN Wave 2A
Telegram handler for signal monitoring.
Receives signals from Alpha TrendFlow.
No trades executed. Read-only.
"""
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler
from data.market_fetcher import fetch_ohlcv, is_supported
from engines.alpha_trendflow import generate_signal

logger = logging.getLogger(__name__)

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate signal for a given pair"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /signal BTCUSDT\n"
            "Supported pairs: BTC, ETH, BNB, SOL, ADA, XRP (all USDT)"
        )
        return
    
    symbol_raw = context.args[0].upper()
    if not is_supported(symbol_raw):
        await update.message.reply_text(f"❌ Pair {symbol_raw} not supported")
        return
    
    # Normalize symbol
    if '/' not in symbol_raw:
        symbol = symbol_raw.replace('USDT', '/USDT') if 'USDT' in symbol_raw else symbol_raw + '/USDT'
    else:
        symbol = symbol_raw
    
    await update.message.reply_text(f"📊 Fetching signal for {symbol}...")
    
    try:
        df_4h = await fetch_ohlcv(symbol, '4h', limit=100)
        df_1h = await fetch_ohlcv(symbol, '1h', limit=100)
        df_15m = await fetch_ohlcv(symbol, '15m', limit=100)
        
        result = generate_signal(df_4h, df_1h, df_15m)
        
        msg = f"""
🔔 **{symbol} Signal**
━━━━━━━━━━━━━━━━━━━━
Signal: **{result['signal']}**
Score: **{result['score']}/40**
Regime: {result.get('regime', 'N/A')}
Tradeable: {'✅ YES' if result.get('tradeable') else '❌ NO'}

📈 Breakdown:
"""
        if 'score_breakdown' in result:
            for key, val in result['score_breakdown'].items():
                msg += f"  • {key}: {val}/40\n"
        
        msg += f"\n💬 Reason: {result.get('reason', 'N/A')}"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        logger.info(f"Signal generated for {symbol}: {result['signal']}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Signal generation error for {symbol}: {e}")

async def regime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check market regime for a pair"""
    if not context.args:
        await update.message.reply_text("Usage: /regime BTCUSDT")
        return
    
    symbol_raw = context.args[0].upper()
    if not is_supported(symbol_raw):
        await update.message.reply_text(f"❌ Pair {symbol_raw} not supported")
        return
    
    if '/' not in symbol_raw:
        symbol = symbol_raw.replace('USDT', '/USDT') if 'USDT' in symbol_raw else symbol_raw + '/USDT'
    else:
        symbol = symbol_raw
    
    try:
        df_4h = await fetch_ohlcv(symbol, '4h', limit=100)
        from engines.regime_classifier import classify_regime
        regime = classify_regime(df_4h)
        
        msg = f"""
📊 **{symbol} Market Regime**
━━━━━━━━━━━━━━━━━━━━
Regime: **{regime['regime']}**
Confidence: {regime['confidence']}%
ATR %: {regime['atr_pct']}%
Note: {regime['note']}
"""
        await update.message.reply_text(msg, parse_mode='Markdown')
        logger.info(f"Regime check for {symbol}: {regime['regime']}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Regime check error for {symbol}: {e}")

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get detailed confidence score breakdown"""
    if not context.args:
        await update.message.reply_text("Usage: /score BTCUSDT")
        return
    
    symbol_raw = context.args[0].upper()
    if not is_supported(symbol_raw):
        await update.message.reply_text(f"❌ Pair {symbol_raw} not supported")
        return
    
    if '/' not in symbol_raw:
        symbol = symbol_raw.replace('USDT', '/USDT') if 'USDT' in symbol_raw else symbol_raw + '/USDT'
    else:
        symbol = symbol_raw
    
    try:
        df_4h = await fetch_ohlcv(symbol, '4h', limit=100)
        from engines.regime_classifier import classify_regime
        from engines.confidence_engine import calculate_score
        
        regime = classify_regime(df_4h)
        score_data = calculate_score(df_4h, regime)
        
        msg = f"""
💯 **{symbol} Confidence Score**
━━━━━━━━━━━━━━━━━━━━
Total: **{score_data['total']}/40**
Verdict: {score_data['verdict']}

📊 Breakdown:
"""
        for key, val in score_data['breakdown'].items():
            msg += f"  • {key}: {val}\n"
        
        msg += "\n📝 Details:\n"
        for key, reason in score_data['reasons'].items():
            msg += f"  {reason}\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        logger.info(f"Score check for {symbol}: {score_data['total']}/40")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Score check error for {symbol}: {e}")

def register_signals(application: Application) -> None:
    """Register signal handlers with the Telegram application"""
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("regime", regime_command))
    application.add_handler(CommandHandler("score", score_command))
    logger.info("Signal handlers registered: /signal, /regime, /score")
