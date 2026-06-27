"""
tradingview_service.py - WAVE 3C
TradingView Integration
Sends signals with chart drawings to TradingView.
"""
import logging
import os
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TradingViewSignal:
    """TradingView signal data."""
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry: float
    stop_loss: float
    take_profit: float
    timeframe: str = '1H'
    score: int = 0
    regime: str = 'N/A'
    setup_type: str = 'N/A'
    atr: float = 0.0
    trend: str = 'N/A'


class TradingViewService:
    """
    TradingView integration service.
    Sends signals via webhook and generates Pine Script.
    """
    
    def __init__(self):
        self.webhook_url = os.getenv("TRADINGVIEW_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
    
    def is_enabled(self) -> bool:
        return self.enabled
    
    async def send_signal(self, signal: TradingViewSignal) -> bool:
        """
        Send signal to TradingView webhook.
        
        Args:
            signal: TradingViewSignal with trade details
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.info("TradingView webhook not configured")
            return False
        
        import aiohttp
        
        # TradingView alert format
        payload = {
            "symbol": signal.symbol,
            "action": signal.direction,
            "entry": signal.entry,
            "stop": signal.stop_loss,
            "limit": signal.take_profit,
            "score": signal.score,
            "regime": signal.regime,
            "setup": signal.setup_type,
            "timeframe": signal.timeframe,
            "comment": f"Titan {signal.setup_type} | {signal.regime} | {signal.score}/40"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"TradingView signal sent: {signal.symbol} {signal.direction}")
                        return True
                    else:
                        logger.error(f"TradingView webhook failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"TradingView webhook error: {e}")
            return False
    
    def generate_pine_script(self, signal: TradingViewSignal) -> str:
        """
        Generate Pine Script v5 for chart drawings.
        
        Args:
            signal: TradingViewSignal with trade details
            
        Returns:
            Pine Script code
        """
        direction = 1 if signal.direction == "LONG" else -1
        
        return f'''//@version=5
strategy("Titan Signal - {signal.symbol}", 
     overlay=true, 
     default_qty_type=strategy.percent_of_equity, 
     default_qty_value=10,
     commission_type=strategy.commission.percent,
     commission_value=0.1)

// ===== INPUTS =====
var inputEntry    = {signal.entry}
var inputStop     = {signal.stop_loss}
var inputTarget   = {signal.take_profit}
var inputScore    = {signal.score}
var inputRegime   = "{signal.regime}"
var inputSetup    = "{signal.setup_type}"
var inputTrend    = "{signal.trend}"

// ===== PLOT LEVELS =====
plot(inputEntry, "Entry", color.blue, 2, plot.style_linebr)
plot(inputStop, "Stop Loss", color.red, 2, plot.style_linebr)
plot(inputTarget, "Take Profit", color.green, 2, plot.style_linebr)

// ===== FILL ZONE =====
fill(plot(close), plot(inputEntry), color.new(color.blue, 90), title="Entry Zone")

// ===== SHAPES =====
plotshape(close, title="Current Price", 
     location=location.abovebar, 
     color=color.orange, 
     style=shape.triangleup, 
     size=size.tiny)

// ===== LABELS =====
label.new(bar_index, low, "ENTRY\\n$" + str.tostring(inputEntry, "#.##"), 
     color=color.blue, textcolor=color.white, 
     style=label.style_label_up, size=size.small)

label.new(bar_index, inputStop, "STOP\\n$" + str.tostring(inputStop, "#.##"), 
     color=color.red, textcolor=color.white, 
     style=label.style_label_down, size=size.small)

label.new(bar_index, inputTarget, "TARGET\\n$" + str.tostring(inputTarget, "#.##"), 
     color=color.green, textcolor=color.white, 
     style=label.style_label_up, size=size.small)

// ===== SIGNAL INFO =====
var table infoTable = table.new(position.top_right, 2, 6, 
     bgcolor=color.new(color.gray, 90))

if barstate.islast
    table.cell(infoTable, 0, 0, "TITAN SIGNAL", 
         text_color=color.white, text_size=size.small)
    table.cell(infoTable, 1, 0, "{signal.direction}", 
         text_color={'color.green' if signal.direction == 'LONG' else 'color.red'}, 
         text_size=size.small)
    table.cell(infoTable, 0, 1, "Score", text_color=color.white, text_size=size.tiny)
    table.cell(infoTable, 1, 1, str.tostring(inputScore) + "/40", text_color=color.yellow, text_size=size.tiny)
    table.cell(infoTable, 0, 2, "Regime", text_color=color.white, text_size=size.tiny)
    table.cell(infoTable, 1, 2, inputRegime, text_color=color.orange, text_size=size.tiny)
    table.cell(infoTable, 0, 3, "Setup", text_color=color.white, text_size=size.tiny)
    table.cell(infoTable, 1, 3, inputSetup, text_color=color.orange, text_size=size.tiny)
    table.cell(infoTable, 0, 4, "Trend", text_color=color.white, text_size=size.tiny)
    table.cell(infoTable, 1, 4, inputTrend, text_color=color.orange, text_size=size.tiny)
    table.cell(infoTable, 0, 5, "Timeframe", text_color=color.white, text_size=size.tiny)
    table.cell(infoTable, 1, 5, "{signal.timeframe}", text_color=color.orange, text_size=size.tiny)

// ===== TREND ARROW =====
plotshape({'close > inputEntry' if signal.direction == 'LONG' else 'close < inputEntry'}, 
     title="In Profit", location=location.abovebar, 
     color=color.green, style=shape.arrowup, size=size.tiny)

plotshape({'close < inputEntry' if signal.direction == 'LONG' else 'close > inputEntry'}, 
     title="Against", location=location.belowbar, 
     color=color.red, style=shape.arrowdown, size=size.tiny)

// ===== ALERTS =====
alertcondition(close crosses below inputStop, "Stop Loss Hit", 
     "Titan: Stop Loss hit on {signal.symbol}")
alertcondition(close crosses above inputTarget, "Take Profit Hit", 
     "Titan: Take Profit hit on {signal.symbol}")
alertcondition(close crosses {signal.direction == 'LONG' and 'above' or 'below'} inputEntry, 
     "Entry Zone", "Titan: Price in entry zone on {signal.symbol}")

// © Titan Trading Intelligence
'''
    
    def format_signal_message(self, signal: TradingViewSignal) -> str:
        """
        Format signal as Telegram message.
        
        Args:
            signal: TradingViewSignal
            
        Returns:
            Formatted message string
        """
        emoji = "🟢" if signal.direction == "LONG" else "🔴"
        
        # Calculate R:R
        risk = abs(signal.entry - signal.stop_loss)
        reward = abs(signal.take_profit - signal.entry)
        rr = reward / risk if risk > 0 else 0
        
        risk_pct = (risk / signal.entry) * 100
        reward_pct = (reward / signal.entry) * 100
        
        lines = [
            f"🚨 TITAN SIGNAL: {signal.symbol}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Direction: {emoji} {signal.direction}",
            f"Score: {signal.score}/40",
            f"Regime: {signal.regime}",
            f"Setup: {signal.setup_type}",
            f"Trend: {signal.trend}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📥 Entry: ${signal.entry:,.2f}",
            f"🛑 Stop: ${signal.stop_loss:,.2f} (-{risk_pct:.2f}%)",
            f"🎯 Target: ${signal.take_profit:,.2f} (+{reward_pct:.2f}%)",
            f"📊 R:R = 1:{rr:.1f}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Timeframe: {signal.timeframe}",
            f"ATR: {signal.atr:.2f}%",
            "━━━━━━━━━━━━━━━━━━━━",
            "⚠️ Paper mode. Use on TradingView for manual trading.",
            "━━━━━━━━━━━━━━━━━━━━",
            "📈 TradingView Script:",
            "```",
            self.generate_pine_script(signal)[:500] + "...",
            "```",
        ]
        
        return "\n".join(lines)
    
    def format_simple_signal(self, signal: TradingViewSignal) -> str:
        """Format simple signal for quick view."""
        emoji = "🟢" if signal.direction == "LONG" else "🔴"
        
        risk = abs(signal.entry - signal.stop_loss)
        reward = abs(signal.take_profit - signal.entry)
        rr = reward / risk if risk > 0 else 0
        
        return f"""{emoji} {signal.symbol} {signal.direction}

Entry: ${signal.entry:,.2f}
Stop: ${signal.stop_loss:,.2f}
Target: ${signal.take_profit:,.2f}

R:R = 1:{rr:.1f} | Score: {signal.score}/40
{signal.setup_type} | {signal.regime}

#Titan #{signal.symbol.replace('USDT','').replace('USD','')}"""


# Global instance
_tradingview_service: Optional[TradingViewService] = None


def get_tradingview_service() -> TradingViewService:
    """Get TradingView service instance."""
    global _tradingview_service
    if _tradingview_service is None:
        _tradingview_service = TradingViewService()
    return _tradingview_service