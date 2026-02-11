#!/usr/bin/env python3
"""
Backtest EMA crossover strategy on historical data from database
Shows what profit we could have made with our strategy
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict

# DB config
DB_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST', 'localhost'),
    'port': int(os.environ.get('POSTGRES_PORT', '5432')),
    'dbname': os.environ.get('POSTGRES_DB', 'trading_bot'),
    'user': os.environ.get('POSTGRES_USER'),
    'password': os.environ.get('POSTGRES_PASSWORD'),
}

# Strategy config
STRATEGY_CONFIG = {
    'initial_capital': 10000.0,  # Starting capital
    'commission_percent': 0.0,    # 0% for Alpaca (можно изменить на 0.1% для реалистичности)
    'position_size_percent': 100,  # Use 100% of capital per trade
    'ema_short': 5,
    'ema_long': 20,
    'confirmation_percent': 0.75,  # Need +0.75% above crossover to confirm
}


class Trade:
    def __init__(self, symbol, entry_price, entry_time, shares):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.shares = shares
        self.exit_price = None
        self.exit_time = None
        self.pnl = 0.0
        self.pnl_percent = 0.0
    
    def close(self, exit_price, exit_time, commission_percent):
        self.exit_price = exit_price
        self.exit_time = exit_time
        
        entry_value = self.shares * self.entry_price
        exit_value = self.shares * self.exit_price
        
        entry_commission = entry_value * (commission_percent / 100)
        exit_commission = exit_value * (commission_percent / 100)
        
        self.pnl = exit_value - entry_value - entry_commission - exit_commission
        self.pnl_percent = (self.pnl / entry_value) * 100
        
        return self.pnl


def calculate_ema(prices, period):
    """Calculate EMA for given prices. Returns full-length array with None for first period-1 values"""
    if len(prices) < period:
        return [None] * len(prices)
    
    ema = [None] * (period - 1)  # Fill first period-1 values with None
    multiplier = 2 / (period + 1)
    
    # Initial SMA
    sma = sum(prices[:period]) / period
    ema.append(sma)
    
    # Calculate EMA for rest
    for i in range(period, len(prices)):
        ema_val = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(ema_val)
    
    return ema


def backtest_strategy(symbol, config=None, start_time=None, window_hours=None):
    """Run backtest for given symbol and period"""
    if config is None:
        config = STRATEGY_CONFIG
    
    if not start_time or not window_hours:
        print(f"Error: start_time and window_hours are required")
        return None
    
    print(f"\n{'='*70}")
    print(f"BACKTESTING: {symbol}")
    print(f"{'='*70}")
    print(f"Initial Capital: ${config['initial_capital']:,.2f}")
    print(f"Commission: {config['commission_percent']}%")
    print(f"Position Size: {config['position_size_percent']}%")
    print(f"EMA: {config['ema_short']}/{config['ema_long']} with {config['confirmation_percent']}% confirmation")
    print(f"{'='*70}\n")
    
    # Fetch historical data (only close prices)
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Use specific time window
    from datetime import datetime, timedelta
    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_dt = start_dt + timedelta(hours=window_hours)
    
    # Load extra data before start_time for EMA warmup (1 day earlier)
    warmup_start_dt = start_dt - timedelta(days=1)
    
    cursor.execute(
        """
        SELECT timestamp, close_price
        FROM ema_snapshots
        WHERE symbol = %s
          AND close_price IS NOT NULL
          AND timestamp >= %s
          AND timestamp <= %s
        ORDER BY timestamp ASC
        """,
        (symbol.upper(), warmup_start_dt, end_dt)
        )
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not rows:
        print(f"No data found for {symbol}")
        return None
    
    print(f"Loaded {len(rows)} data points (including warmup period)\n")
    
    # Find index where actual backtest window starts
    backtest_start_idx = 0
    for i, (ts, _) in enumerate(rows):
        if ts >= start_dt:
            backtest_start_idx = i
            break
    
    print(f"Warmup period: {backtest_start_idx} data points")
    print(f"Backtest period: {len(rows) - backtest_start_idx} data points\n")
    
    # Calculate EMAs on ALL data (including warmup)
    close_prices = [float(r[1]) for r in rows]
    ema_short_values = calculate_ema(close_prices, config['ema_short'])
    ema_long_values = calculate_ema(close_prices, config['ema_long'])
    
    # Simulate trading
    capital = config['initial_capital']
    position = None  # Current open trade
    trades = []  # Completed trades
    equity_curve = [capital]
    
    state = 'flat'  # flat, in_position
    
    for i, (timestamp, close) in enumerate(rows):
        # Skip warmup period - only backtest on requested window
        if i < backtest_start_idx:
            continue
            
        # Convert Decimal to float
        close = float(close) if close else None
        ema_short = ema_short_values[i]
        ema_long = ema_long_values[i]
        
        if not close or not ema_short or not ema_long:
            continue
        
        # Detect crossover manually (more accurate than stored value)
        crossover = 'none'
        crossover_price = close  # Default to current close
        
        if i > 0:
            prev_close = float(rows[i-1][1]) if rows[i-1][1] else None
            prev_ema_short = ema_short_values[i-1]
            prev_ema_long = ema_long_values[i-1]
            
            if prev_ema_short and prev_ema_long and prev_close:
                # Calculate exact crossover price using linear interpolation
                if prev_ema_short <= prev_ema_long and ema_short > ema_long:
                    crossover = 'bullish'
                    # Interpolate price at crossover point
                    ema_short_diff = ema_short - prev_ema_short
                    ema_long_diff = ema_long - prev_ema_long
                    if (ema_short_diff - ema_long_diff) != 0:
                        ratio = (prev_ema_long - prev_ema_short) / (ema_short_diff - ema_long_diff)
                        ratio = max(0, min(1, ratio))  # Clamp between 0 and 1
                        crossover_price = prev_close + ratio * (close - prev_close)
                    
                elif prev_ema_short >= prev_ema_long and ema_short < ema_long:
                    crossover = 'bearish'
                    # Interpolate price at crossover point
                    ema_short_diff = ema_short - prev_ema_short
                    ema_long_diff = ema_long - prev_ema_long
                    if (ema_short_diff - ema_long_diff) != 0:
                        ratio = (prev_ema_long - prev_ema_short) / (ema_short_diff - ema_long_diff)
                        ratio = max(0, min(1, ratio))  # Clamp between 0 and 1
                        crossover_price = prev_close + ratio * (close - prev_close)
        
        # State machine
        if state == 'flat':
            if crossover == 'bullish':
                # BUY at interpolated crossover price
                shares = int((capital * config['position_size_percent'] / 100) / crossover_price)
                if shares > 0:
                    position = Trade(symbol, crossover_price, timestamp, shares)
                    capital -= (shares * crossover_price)  # Deduct capital
                    state = 'in_position'
                    print(f"[{timestamp}] ✅ BUY {shares} shares @ ${crossover_price:.2f} (bullish crossover: EMA{config['ema_short']} ${ema_short:.2f} > EMA{config['ema_long']} ${ema_long:.2f}, close ${close:.2f})")
                    print(f"             Capital remaining: ${capital:,.2f}")
        
        elif state == 'in_position':
            if crossover == 'bearish':
                # SELL at interpolated crossover price
                pnl = position.close(crossover_price, timestamp, config['commission_percent'])
                capital += (position.shares * crossover_price)  # Return capital + profit/loss
                trades.append(position)
                
                print(f"[{timestamp}] 💰 SELL {position.shares} shares @ ${crossover_price:.2f} (bearish crossover: EMA{config['ema_short']} ${ema_short:.2f} < EMA{config['ema_long']} ${ema_long:.2f}, close ${close:.2f})")
                print(f"             P&L: ${pnl:,.2f} ({position.pnl_percent:+.2f}%)")
                print(f"             Capital: ${capital:,.2f}\n")
                
                position = None
                state = 'flat'
        
        equity_curve.append(capital + (position.shares * close if position else 0))
    
    # Close any open position at end
    if position:
        final_price = rows[-1][1]
        pnl = position.close(final_price, rows[-1][0], config['commission_percent'])
        capital += (position.shares * final_price)
        trades.append(position)
        print(f"[{rows[-1][0]}] 🔚 Position closed at end: ${final_price:.2f}")
        print(f"             P&L: ${pnl:,.2f} ({position.pnl_percent:+.2f}%)\n")
    
    # Calculate statistics
    final_capital = capital
    total_return = final_capital - config['initial_capital']
    total_return_percent = (total_return / config['initial_capital']) * 100
    
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]
    
    win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
    avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    max_equity = max(equity_curve)
    max_drawdown = min(equity_curve) - max_equity
    max_drawdown_percent = (max_drawdown / max_equity * 100) if max_equity > 0 else 0
    
    # Print results
    print(f"\n{'='*70}")
    print(f"BACKTEST RESULTS: {symbol}")
    print(f"{'='*70}")
    print(f"Period: {rows[0][0]} → {rows[-1][0]}")
    print(f"Data Points: {len(rows)}")
    print(f"\n--- PERFORMANCE ---")
    print(f"Initial Capital:    ${config['initial_capital']:>12,.2f}")
    print(f"Final Capital:      ${final_capital:>12,.2f}")
    print(f"Total Return:       ${total_return:>12,.2f} ({total_return_percent:+.2f}%)")
    print(f"Max Equity:         ${max_equity:>12,.2f}")
    print(f"Max Drawdown:       ${max_drawdown:>12,.2f} ({max_drawdown_percent:.2f}%)")
    print(f"\n--- TRADES ---")
    print(f"Total Trades:       {len(trades):>12}")
    print(f"Winning Trades:     {len(winning_trades):>12} ({win_rate:.1f}%)")
    print(f"Losing Trades:      {len(losing_trades):>12}")
    print(f"Average Win:        ${avg_win:>12,.2f}")
    print(f"Average Loss:       ${avg_loss:>12,.2f}")
    
    if trades:
        best_trade = max(trades, key=lambda t: t.pnl)
        worst_trade = min(trades, key=lambda t: t.pnl)
        print(f"Best Trade:         ${best_trade.pnl:>12,.2f} ({best_trade.pnl_percent:+.2f}%)")
        print(f"Worst Trade:        ${worst_trade.pnl:>12,.2f} ({worst_trade.pnl_percent:+.2f}%)")
    
    print(f"{'='*70}\n")
    
    return {
        'symbol': symbol,
        'initial_capital': config['initial_capital'],
        'final_capital': final_capital,
        'total_return': total_return,
        'total_return_percent': total_return_percent,
        'trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_drawdown,
        'max_drawdown_percent': max_drawdown_percent,
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Backtest EMA crossover strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Backtest NVDA for specific time window
  %(prog)s --symbol NVDA --start-time "2026-01-02T16:00:00Z" --window-hours 6
  
  # Backtest multiple symbols
  %(prog)s --batch NVDA AAPL TSLA --start-time "2026-01-02T16:00:00Z" --window-hours 24
  
  # Custom config
  %(prog)s --symbol NVDA --capital 50000 --commission 0.1 --start-time "2026-01-02T16:00:00Z" --window-hours 8
        '''
    )
    
    parser.add_argument('--symbol', default='NVDA', help='Stock symbol (default: NVDA)')
    parser.add_argument('--batch', nargs='+', help='Backtest multiple symbols')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital (default: 10000)')
    parser.add_argument('--commission', type=float, default=0.0, help='Commission percent (default: 0.0)')
    parser.add_argument('--position-size', type=float, default=100, help='Position size percent (default: 100)')
    parser.add_argument('--ema-short', type=int, default=5, help='EMA short period (default: 5)')
    parser.add_argument('--ema-long', type=int, default=50, help='EMA long period (default: 50)')
    parser.add_argument('--confirmation', type=float, default=0.75, help='Confirmation percent (default: 0.75)')
    parser.add_argument('--start-time', type=str, required=True, help='Start time in ISO format (required)')
    parser.add_argument('--window-hours', type=int, required=True, help='Window hours from start time (required)')
    
    args = parser.parse_args()
    
    config = STRATEGY_CONFIG.copy()
    config['initial_capital'] = args.capital
    config['commission_percent'] = args.commission
    config['position_size_percent'] = args.position_size
    config['ema_short'] = args.ema_short
    config['ema_long'] = args.ema_long
    config['confirmation_percent'] = args.confirmation
    
    if args.batch:
        results = []
        for symbol in args.batch:
            result = backtest_strategy(symbol, config, args.start_time, args.window_hours)
            if result:
                results.append(result)
        
        # Summary
        if results:
            print(f"\n{'='*70}")
            print("SUMMARY")
            print(f"{'='*70}")
            total_capital = sum(r['initial_capital'] for r in results)
            total_final = sum(r['final_capital'] for r in results)
            total_return = total_final - total_capital
            total_return_pct = (total_return / total_capital * 100) if total_capital > 0 else 0
            
            print(f"Total Initial Capital: ${total_capital:,.2f}")
            print(f"Total Final Capital:   ${total_final:,.2f}")
            print(f"Total Return:          ${total_return:,.2f} ({total_return_pct:+.2f}%)")
            print(f"Total Trades:          {sum(r['trades'] for r in results)}")
            print(f"{'='*70}\n")
    else:
        backtest_strategy(args.symbol, config, args.start_time, args.window_hours)
    
    print("✅ Backtest complete!")
