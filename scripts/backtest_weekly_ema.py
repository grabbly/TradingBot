#!/usr/bin/env python3
"""
Backtest Weekly EMA Crossover Strategy
- Buy when EMA10 crosses above EMA30 (on weekly close)
- Sell when EMA10 crosses below EMA30
- Optional: Filter with EMA50 (only trade above EMA50)
"""

import os
import psycopg2
from datetime import datetime

# DB config
DB_CONFIG = {
    'host': os.environ.get('PGHOST', 'localhost'),
    'port': int(os.environ.get('PGPORT', '5432')),
    'dbname': os.environ.get('PGDATABASE', 'trading_bot'),
    'user': os.environ.get('PGUSER', 'n8n_user'),
    'password': os.environ.get('PGPASSWORD', '***REMOVED***'),
}

STRATEGY_CONFIG = {
    'initial_capital': 10000,
    'commission_percent': 0.0,
    'ema_short': 10,
    'ema_long': 30,
    'ema_filter': 50,  # Only trade above EMA50 (0 to disable)
    'use_filter': True,
}


class Trade:
    def __init__(self, symbol, entry_price, entry_date, shares):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.shares = shares
        self.exit_price = None
        self.exit_date = None
        self.pnl = 0
        self.pnl_percent = 0
    
    def close(self, exit_price, exit_date, commission_percent=0):
        self.exit_price = exit_price
        self.exit_date = exit_date
        
        gross_pnl = (exit_price - self.entry_price) * self.shares
        commission = (self.entry_price * self.shares + exit_price * self.shares) * (commission_percent / 100)
        self.pnl = gross_pnl - commission
        self.pnl_percent = (self.pnl / (self.entry_price * self.shares)) * 100
        
        return self.pnl


def calculate_ema(prices, period):
    """Calculate EMA for given prices"""
    if len(prices) < period:
        return [None] * len(prices)
    
    ema = [None] * (period - 1)
    multiplier = 2 / (period + 1)
    
    # Initial SMA
    sma = sum(prices[:period]) / period
    ema.append(sma)
    
    # Calculate EMA for rest
    for i in range(period, len(prices)):
        ema_val = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(ema_val)
    
    return ema


def backtest_strategy(symbol, timeframe='1wk', config=None, start_date=None, end_date=None):
    """Run backtest for given symbol on weekly timeframe"""
    if config is None:
        config = STRATEGY_CONFIG
    
    print(f"\n{'='*70}")
    print(f"BACKTESTING: {symbol} - Weekly EMA Crossover Strategy")
    print(f"{'='*70}")
    print(f"Initial Capital: ${config['initial_capital']:,.2f}")
    print(f"Commission: {config['commission_percent']}%")
    print(f"Timeframe: {timeframe}")
    print(f"EMA: {config['ema_short']}/{config['ema_long']}")
    if config['use_filter']:
        print(f"Filter: Only trade above EMA{config['ema_filter']}")
    print(f"{'='*70}\n")
    
    # Fetch historical data (weekly bars)
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Load weekly data - take last day of each week (Friday or last trading day)
    sql = """
        WITH weekly_data AS (
            SELECT 
                DATE_TRUNC('week', timestamp) as week_start,
                MAX(timestamp) as week_end,
                (ARRAY_AGG(close_price ORDER BY timestamp DESC))[1] as close_price
            FROM ema_snapshots
            WHERE symbol = %s
              AND close_price IS NOT NULL
              {date_filter}
            GROUP BY DATE_TRUNC('week', timestamp)
            ORDER BY week_start
        )
        SELECT week_end as timestamp, close_price
        FROM weekly_data
        ORDER BY timestamp ASC
    """
    
    params = [symbol.upper()]
    date_filter = ""
    
    if start_date:
        date_filter += " AND timestamp >= %s"
        params.append(start_date)
    if end_date:
        date_filter += " AND timestamp <= %s"
        params.append(end_date)
    
    sql = sql.format(date_filter=date_filter)
    cursor.execute(sql, tuple(params))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not rows:
        print(f"No data found for {symbol}")
        return None
    
    min_bars = config['ema_filter'] if config['use_filter'] else config['ema_long']
    if len(rows) < min_bars:
        print(f"Not enough data. Need at least {min_bars} bars, got {len(rows)}")
        return None
    
    print(f"Loaded {len(rows)} weekly bars")
    print(f"Period: {rows[0][0].strftime('%Y-%m-%d')} to {rows[-1][0].strftime('%Y-%m-%d')}\n")
    
    # Extract prices
    timestamps = [r[0] for r in rows]
    close_prices = [float(r[1]) for r in rows]
    
    # Calculate EMAs
    ema_short = calculate_ema(close_prices, config['ema_short'])
    ema_long = calculate_ema(close_prices, config['ema_long'])
    ema_filter = calculate_ema(close_prices, config['ema_filter']) if config['use_filter'] else None
    
    # Backtest logic
    capital = config['initial_capital']
    position = None
    state = 'flat'
    trades = []
    equity_curve = [capital]
    
    for i in range(1, len(rows)):
        timestamp = timestamps[i]
        close = close_prices[i]
        ema_s = ema_short[i]
        ema_l = ema_long[i]
        ema_f = ema_filter[i] if ema_filter else None
        
        if not ema_s or not ema_l:
            equity_curve.append(capital + (position.shares * close if position else 0))
            continue
        
        if config['use_filter'] and (not ema_f or close < ema_f):
            # Below filter - skip or exit if in position
            if state == 'in_position':
                pnl = position.close(close, timestamp, config['commission_percent'])
                capital += (position.shares * close)
                trades.append(position)
                
                print(f"[{timestamp.strftime('%Y-%m-%d')}] ⚠️  EXIT (below EMA{config['ema_filter']}) - SELL {position.shares} shares @ ${close:.2f}")
                print(f"             P&L: ${pnl:,.2f} ({position.pnl_percent:+.2f}%)")
                print(f"             Capital: ${capital:,.2f}\n")
                
                position = None
                state = 'flat'
            
            equity_curve.append(capital + (position.shares * close if position else 0))
            continue
        
        # Detect crossover
        prev_ema_s = ema_short[i-1]
        prev_ema_l = ema_long[i-1]
        
        if not prev_ema_s or not prev_ema_l:
            equity_curve.append(capital + (position.shares * close if position else 0))
            continue
        
        # Bullish crossover (EMA10 crosses above EMA30)
        if prev_ema_s <= prev_ema_l and ema_s > ema_l:
            if state == 'flat':
                # BUY at next week's open (use close as proxy)
                shares = int(capital / close)
                if shares > 0:
                    position = Trade(symbol, close, timestamp, shares)
                    capital -= (shares * close)
                    state = 'in_position'
                    print(f"[{timestamp.strftime('%Y-%m-%d')}] 🟢 BULLISH CROSS - BUY {shares} shares @ ${close:.2f}")
                    print(f"             EMA{config['ema_short']}: ${ema_s:.2f}, EMA{config['ema_long']}: ${ema_l:.2f}")
                    if config['use_filter']:
                        print(f"             EMA{config['ema_filter']}: ${ema_f:.2f} (filter: OK)")
                    print(f"             Capital remaining: ${capital:,.2f}\n")
        
        # Bearish crossover (EMA10 crosses below EMA30)
        elif prev_ema_s >= prev_ema_l and ema_s < ema_l:
            if state == 'in_position':
                # SELL at next week's open (use close as proxy)
                pnl = position.close(close, timestamp, config['commission_percent'])
                capital += (position.shares * close)
                trades.append(position)
                
                print(f"[{timestamp.strftime('%Y-%m-%d')}] 🔴 BEARISH CROSS - SELL {position.shares} shares @ ${close:.2f}")
                print(f"             EMA{config['ema_short']}: ${ema_s:.2f}, EMA{config['ema_long']}: ${ema_l:.2f}")
                print(f"             P&L: ${pnl:,.2f} ({position.pnl_percent:+.2f}%)")
                print(f"             Capital: ${capital:,.2f}\n")
                
                position = None
                state = 'flat'
        
        equity_curve.append(capital + (position.shares * close if position else 0))
    
    # Close any open position at end
    if position:
        final_price = close_prices[-1]
        pnl = position.close(final_price, timestamps[-1], config['commission_percent'])
        capital += (position.shares * final_price)
        trades.append(position)
        print(f"[{timestamps[-1].strftime('%Y-%m-%d')}] 🔚 Position closed at end: ${final_price:.2f}")
        print(f"             P&L: ${pnl:,.2f} ({position.pnl_percent:+.2f}%)\n")
    
    # Statistics
    final_capital = capital
    total_return = final_capital - config['initial_capital']
    total_return_pct = (total_return / config['initial_capital']) * 100
    
    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")
    print(f"Initial Capital:  ${config['initial_capital']:,.2f}")
    print(f"Final Capital:    ${final_capital:,.2f}")
    print(f"Total Return:     ${total_return:,.2f} ({total_return_pct:+.2f}%)")
    print(f"Total Trades:     {len(trades)}")
    
    if trades:
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        print(f"Winning Trades:   {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"Losing Trades:    {len(losing_trades)}")
        if winning_trades:
            print(f"Average Win:      ${avg_win:,.2f}")
        if losing_trades:
            print(f"Average Loss:     ${avg_loss:,.2f}")
        
        # Max drawdown
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_percent = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_percent = drawdown_pct
        
        print(f"Max Drawdown:     ${max_drawdown:,.2f} ({max_drawdown_percent:.2f}%)")
    
    # Buy & Hold comparison
    buy_hold_return = ((close_prices[-1] - close_prices[0]) / close_prices[0]) * 100
    print(f"\nBuy & Hold:       {buy_hold_return:+.2f}%")
    print(f"Strategy Alpha:   {total_return_pct - buy_hold_return:+.2f}%")
    
    print(f"{'='*70}\n")
    
    return {
        'symbol': symbol,
        'initial_capital': config['initial_capital'],
        'final_capital': final_capital,
        'total_return': total_return,
        'total_return_pct': total_return_pct,
        'trades': len(trades),
        'win_rate': win_rate if trades else 0,
        'max_drawdown': max_drawdown if trades else 0,
        'max_drawdown_percent': max_drawdown_percent if trades else 0,
        'buy_hold_return': buy_hold_return,
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Backtest Weekly EMA Crossover strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Backtest SPY with default 10/30 EMA
  %(prog)s --symbol SPY
  
  # Backtest without EMA50 filter
  %(prog)s --symbol SPY --no-filter
  
  # Backtest multiple symbols
  %(prog)s --batch SPY QQQ
  
  # Custom parameters
  %(prog)s --symbol SPY --ema-short 10 --ema-long 30 --ema-filter 50
        '''
    )
    
    parser.add_argument('--symbol', default='SPY', help='Stock symbol (default: SPY)')
    parser.add_argument('--batch', nargs='+', help='Backtest multiple symbols')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital (default: 10000)')
    parser.add_argument('--commission', type=float, default=0.0, help='Commission percent (default: 0.0)')
    parser.add_argument('--ema-short', type=int, default=10, help='Short EMA period (default: 10)')
    parser.add_argument('--ema-long', type=int, default=30, help='Long EMA period (default: 30)')
    parser.add_argument('--ema-filter', type=int, default=50, help='Filter EMA period (default: 50)')
    parser.add_argument('--no-filter', action='store_true', help='Disable EMA50 filter')
    parser.add_argument('--start-date', type=str, help='Start date YYYY-MM-DD (optional)')
    parser.add_argument('--end-date', type=str, help='End date YYYY-MM-DD (optional)')
    
    args = parser.parse_args()
    
    config = STRATEGY_CONFIG.copy()
    config['initial_capital'] = args.capital
    config['commission_percent'] = args.commission
    config['ema_short'] = args.ema_short
    config['ema_long'] = args.ema_long
    config['ema_filter'] = args.ema_filter
    config['use_filter'] = not args.no_filter
    
    if args.batch:
        results = []
        for symbol in args.batch:
            result = backtest_strategy(symbol, '1wk', config, args.start_date, args.end_date)
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
        backtest_strategy(args.symbol, '1wk', config, args.start_date, args.end_date)
