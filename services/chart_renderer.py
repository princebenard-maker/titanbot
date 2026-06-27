"""
chart_renderer.py - WAVE 2C
Titan Chart Rendering Service
ASCII charts + TradingView webhook integration.
"""
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PriceLevel:
    """Price level annotation."""
    price: float
    label: str
    type: str  # 'entry', 'stop', 'target', 'support', 'resistance'


@dataclass
class SignalChart:
    """Signal chart data."""
    symbol: str
    current_price: float
    timeframe: str
    trend: str  # 'bullish', 'bearish', 'neutral'
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    candles: list = None  # List of (timestamp, open, high, low, close, volume)
    

class ASCIIChartRenderer:
    """
    Renders ASCII charts for Telegram display.
    """
    
    def __init__(self, width: int = 40, height: int = 15):
        self.width = width
        self.height = height
    
    def render(self, chart: SignalChart) -> str:
        """
        Render chart as ASCII art.
        
        Args:
            chart: SignalChart data
            
        Returns:
            ASCII chart string
        """
        if not chart.candles:
            return self._render_simple(chart)
        
        return self._render_candles(chart)
    
    def _render_simple(self, chart: SignalChart) -> str:
        """Render simple price display without candles."""
        emoji = "📈" if chart.trend == "bullish" else "📉" if chart.trend == "bearish" else "➡️"
        
        lines = [
            f"{emoji} {chart.symbol} - {chart.timeframe}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Price: ${chart.current_price:,.2f}",
        ]
        
        if chart.entry:
            lines.append(f"Entry: ${chart.entry:,.2f}")
        if chart.stop_loss:
            sl_pct = ((chart.stop_loss - chart.entry) / chart.entry * 100) if chart.entry else 0
            lines.append(f"Stop: ${chart.stop_loss:,.2f} ({sl_pct:+.1f}%)")
        if chart.take_profit:
            tp_pct = ((chart.take_profit - chart.entry) / chart.entry * 100) if chart.entry else 0
            lines.append(f"Target: ${chart.take_profit:,.2f} ({tp_pct:+.1f}%)")
        
        return "\n".join(lines)
    
    def _render_candles(self, chart: SignalChart) -> str:
        """Render candle chart."""
        candles = chart.candles[-self.width:]
        
        if not candles:
            return self._render_simple(chart)
        
        # Extract prices
        lows = [c[3] for c in candles]  # low
        highs = [c[2] for c in candles]  # high
        
        min_price = min(lows)
        max_price = max(highs)
        price_range = max_price - min_price
        
        if price_range == 0:
            price_range = 1
        
        # Build grid
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]
        
        # Plot candles
        for i, candle in enumerate(candles):
            open_, high, low, close = candle[1:5]
            
            # Price to y position
            def price_to_y(price):
                return int((max_price - price) / price_range * (self.height - 1))
            
            high_y = price_to_y(high)
            low_y = price_to_y(low)
            open_y = price_to_y(open_)
            close_y = price_to_y(close)
            
            # Draw wick
            for y in range(min(high_y, low_y), max(high_y, low_y) + 1):
                if 0 <= y < self.height:
                    grid[y][i] = "│"
            
            # Draw body
            top = min(open_y, close_y)
            bottom = max(open_y, close_y)
            char = "█" if close >= open_ else "▓"
            
            for y in range(top, bottom + 1):
                if 0 <= y < self.height:
                    grid[y][i] = char
        
        # Add levels
        levels = []
        if chart.entry:
            levels.append((chart.entry, "ENTRY", "●"))
        if chart.stop_loss:
            levels.append((chart.stop_loss, "SL", "○"))
        if chart.take_profit:
            levels.append((chart.take_profit, "TP", "◎"))
        
        # Build output
        lines = []
        lines.append(f"📊 {chart.symbol} - {chart.timeframe}")
        lines.append("━" * (self.width + 2))
        
        # Price axis
        for row in grid:
            prices = []
            # Left price
            prices.append("")
            prices.append("".join(row))
        
        # Render
        for i in range(self.height - 1, -1, -1):
            price = max_price - (i / (self.height - 1)) * price_range
            row = "".join(grid[i])
            lines.append(f"${price:>10,.0f} │{row}")
        
        lines.append(" " * 11 + "└" + "─" * self.width)
        
        # Add annotations
        if levels:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for price, label, char in sorted(levels, key=lambda x: x[0], reverse=True):
                lines.append(f"{char} {label}: ${price:,.2f}")
        
        return "\n".join(lines)


class TradingViewWebhook:
    """
    TradingView webhook integration.
    Sends signals to TradingView alerts.
    """
    
    def __init__(self):
        import os
        self.enabled = bool(os.getenv('TRADINGVIEW_WEBHOOK_URL'))
        self.webhook_url = os.getenv('TRADINGVIEW_WEBHOOK_URL')
    
    async def send_signal(
        self,
        symbol: str,
        direction: str,  # 'long' or 'short'
        entry: float,
        stop_loss: float,
        take_profit: float,
        timeframe: str = '1h',
        setup_type: str = None,
        confidence: int = None
    ) -> bool:
        """
        Send signal to TradingView webhook.
        
        Args:
            symbol: Trading pair
            direction: 'long' or 'short'
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            timeframe: Chart timeframe
            setup_type: Setup classification
            confidence: Confidence score
            
        Returns:
            True if sent successfully
        """
        import aiohttp
        
        if not self.enabled:
            logger.info("TradingView webhook not configured")
            return False
        
        # TradingView Pine Script webhook format
        payload = {
            "symbol": symbol,
            "strategy": {
                "action": "BUY" if direction == "long" else "SELL",
                "entry": entry,
                "stop": stop_loss,
                "limit": take_profit,
            },
            "comment": f"Titan {setup_type or 'Signal'} | TF: {timeframe} | Conf: {confidence or 'N/A'}%"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"TradingView webhook sent: {symbol} {direction}")
                        return True
                    else:
                        logger.error(f"TradingView webhook failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"TradingView webhook error: {e}")
            return False
    
    def create_pine_script(self, symbol: str) -> str:
        """
        Generate Pine Script for TradingView chart.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Pine Script v5 code
        """
        return f'''//@version=5
strategy("Titan {symbol}", overlay=true, default_qty_type=strategy.percent_of_equity, default_qty_value=10)

// Get Titan signals from webhook
signalEntry = input.string(title="Entry Signal", defval="")
signalDirection = input.string(title="Direction", defval="long")

// Entry
longCondition = signalDirection == "long" and signalEntry == "entry"
if (longCondition)
    strategy.entry(id="Long", direction=strategy.long)

shortCondition = signalDirection == "short" and signalEntry == "entry"  
if (shortCondition)
    strategy.entry(id="Short", direction=strategy.short)

// Exit
strategy.exit(id="Exit", from_entry="Long", stop=strategy.position_avg_price * 0.98, limit=strategy.position_avg_price * 1.03)
strategy.exit(id="Exit", from_entry="Short", stop=strategy.position_avg_price * 1.02, limit=strategy.position_avg_price * 0.97)

// Plot
plotshape(longCondition, title="Long Signal", location=location.belowbar, color=color.green, style=shape.triangleup, size=size.tiny, text="LONG")
plotshape(shortCondition, title="Short Signal", location=location.abovebar, color=color.red, style=shape.triangledown, size=size.tiny, text="SHORT")
'''


class SignalFormatter:
    """
    Formats signals for display across different channels.
    """
    
    @staticmethod
    def format_for_telegram(
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        score: int,
        regime: str,
        setup_type: str,
        atr: float = None
    ) -> str:
        """Format signal for Telegram."""
        emoji = "🟢" if direction == "LONG" else "🔴"
        
        risk_pct = abs((stop_loss - entry) / entry * 100)
        reward_pct = abs((take_profit - entry) / entry * 100)
        rr_ratio = reward_pct / risk_pct if risk_pct > 0 else 0
        
        msg = [
            f"🚨 TITAN SIGNAL: {symbol}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Direction: {emoji} {direction}",
            f"Score: {score}/40",
            f"Regime: {regime}",
            f"Setup: {setup_type.replace('_', ' ')}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Entry: ${entry:,.2f}",
            f"Stop: ${stop_loss:,.2f} (-{risk_pct:.2f}%)",
            f"Target: ${take_profit:,.2f} (+{reward_pct:.2f}%)",
            f"R:R = 1:{rr_ratio:.1f}",
        ]
        
        if atr:
            msg.append(f"ATR: {atr:.2f}%")
        
        msg.append("━━━━━━━━━━━━━━━━━━━━")
        msg.append("⚠️ Paper mode. Not financial advice.")
        
        return "\n".join(msg)
    
    @staticmethod
    def format_for_group(
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        setup_type: str,
        confidence: int
    ) -> str:
        """Format signal for group broadcast."""
        risk_pct = abs((stop_loss - entry) / entry * 100)
        reward_pct = abs((take_profit - entry) / entry * 100)
        
        emoji = "🟢" if direction == "LONG" else "🔴"
        
        return f"""📊 TITAN SIGNAL

Pair: {symbol}
Direction: {emoji} {direction}
Setup: {setup_type.replace('_', ' ')}
Confidence: {confidence}%

Entry: ${entry:,.2f}
Stop Loss: ${stop_loss:,.2f} (-{risk_pct:.2f}%)
Take Profit: ${take_profit:,.2f} (+{reward_pct:.2f}%)

#Titan #{symbol.replace('USDT','')} #{direction.lower()}"""
    
    @staticmethod
    def format_for_admin(
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        account_balance: float,
        risk_amount: float
    ) -> str:
        """Format signal for admin alert."""
        return f"""⚠️ PAPER TRADE EXECUTED

Pair: {symbol}
Direction: {direction}
Entry: ${entry:,.2f}
Stop: ${stop_loss:,.2f}
Target: ${take_profit:,.2f}

Position Size: ${position_size:,.2f}
Account: ${account_balance:,.2f}
Risk: ${risk_amount:,.2f} (2% max)

Titan is monitoring. Track at /paper_positions"""


# Global instances
_ascii_renderer: ASCIIChartRenderer = None
_tradingview_webhook: TradingViewWebhook = None


def get_ascii_renderer() -> ASCIIChartRenderer:
    global _ascii_renderer
    if _ascii_renderer is None:
        _ascii_renderer = ASCIIChartRenderer()
    return _ascii_renderer


def get_tradingview_webhook() -> TradingViewWebhook:
    global _tradingview_webhook
    if _tradingview_webhook is None:
        _tradingview_webhook = TradingViewWebhook()
    return _tradingview_webhook
