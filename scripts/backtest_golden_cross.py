#!/usr/bin/env python3
"""
Backtest Golden Cross / Death Cross Strategy
- Buy on Golden Cross (SMA50 crosses above SMA200)
- Sell on Death Cross (SMA50 crosses below SMA200)
- Daily timeframe, no stop-loss
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
    'commission_percent': 0.0,  # Commission per trade
    'sma_short': 50,
    'sma_long': 200,
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


def calculate_sma(prices, period):
    """Calculate SMA for given prices"""
    if len(prices) < period:
        return [None] * len(prices)
    
    sma = [None] * (period - 1)
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        sma.append(sum(window) / period)
    
    return sma


def backtest_strategy(symbol, config=None):
    """Run backtest for given symbol"""
    if config is None:
        config = STRATEGY_CONFIG
    
    print(f"\n{'='*70}")
    print(f"BACKTESTING: {symbol} - Golden Cross Strategy")
    print(f"{'='*70}")
    print(f"Initial Capital: ${config['initial_capital']:,.2f}")
    print(f"Commission: {config['commission_percent']}%")
    print(f"SMA: {config['sma_short']}/{config['sma_long']}")
    print(f"{'='*70}\n")
    
    # Fetch historical data (daily bars)
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT timestamp, close_price
        FROM ema_snapshots
        WHERE symbol = %s
          AND close_price IS NOT NULL
        ORDER BY timestamp ASC
        """,
        (symbol.upper(),)
    )
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not rows:
        print(f"No data found for {symbol}")
        return None
    
    if len(rows) < config['sma_long']:
        print(f"Not enough data for SMA{config['sma_long']} calculation. Need at least {config['sma_long']} bars, got {len(rows)}")
        return None
    
    print(f"Loaded {len(rows)} daily bars")
    print(f"Period: {rows[0][0].strftime('%Y-%m-%d')} to {rows[-1][0].strftime('%Y-%m-%d')}\n")
    
    # Extract prices
    timestamps = [r[0] for r in rows]
    close_prices = [float(r[1]) for r in rows]
    
    # Calculate SMAs
    sma_short = calculate_sma(close_prices, config['sma_short'])
    sma_long = calculate_sma(close_prices, config['sma_long'])
    
    # Backtest logic
    capital = config['initial_capital']
    position = None
    state = 'flat'  # 'flat' or 'in_position'
    trades = []
    equity_curve = [capital]
    
    for i in range(1, len(rows)):
        timestamp = timestamps[i]
        close = close_prices[i]
        sma_s = sma_short[i]
        sma_l = sma_long[i]
        
        if not sma_s or not sma_l:
            equity_curve.append(capital + (position.shares * close if position else 0))
            continue
        
        # Detect crossover
        prev_sma_s = sma_short[i-1]
        prev_sma_l = sma_long[i-1]
        
        if not prev_sma_s or not prev_sma_l:
            equity_curve.append(capital + (position.shares * close if position else 0))
            continue
        
        # Golden Cross (bullish)
        if prev_sma_s <= prev_sma_l and sma_s > sma_l:
            if state == 'flat':
                # BUY at next day's open (use close as proxy)
                shares = int(capital / close)
                if shares > 0:
                    position = Trade(symbol, close, timestamp, shares)
                    capital -= (shares * close)
                    state = 'in_position'
                    print(f"[{timestamp.strftime('%Y-%m-%d')}] 🟢 GOLDEN CROSS - BUY {shares} shares @ ${close:.2f}")
                    print(f"             SMA{config['sma_short']}: ${sma_s:.2f}, SMA{config['sma_long']}: ${sma_l:.2f}")
                    print(f"             Capital remaining: ${capital:,.2f}\n")
        
        # Death Cross (bearish)
        elif prev_sma_s >= prev_sma_l and sma_s < sma_l:
            if state == 'in_position':
                # SELL at next day's open (use close as proxy)
                pnl = position.close(close, timestamp, config['commission_percent'])
                capital += (position.shares * close)
                trades.append(position)
                
                print(f"[{timestamp.strftime('%Y-%m-%d')}] 🔴 DEATH CROSS - SELL {position.shares} shares @ ${close:.2f}")
                print(f"             SMA{config['sma_short']}: ${sma_s:.2f}, SMA{config['sma_long']}: ${sma_l:.2f}")
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
        print(f"Average Win:      ${avg_win:,.2f}")
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
        description='Backtest Golden Cross / Death Cross strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Backtest SPY
  %(prog)s --symbol SPY
  
  # Backtest multiple symbols
  %(prog)s --batch SPY QQQ
  
  # Custom capital
  %(prog)s --symbol SPY --capital 100000
        '''
    )
    
    parser.add_argument('--symbol', default='SPY', help='Stock symbol (default: SPY)')
    parser.add_argument('--batch', nargs='+', help='Backtest multiple symbols')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital (default: 10000)')
    parser.add_argument('--commission', type=float, default=0.0, help='Commission percent (default: 0.0)')
    parser.add_argument('--sma-short', type=int, default=50, help='Short SMA period (default: 50)')
    parser.add_argument('--sma-long', type=int, default=200, help='Long SMA period (default: 200)')
    
    args = parser.parse_args()
    
    config = STRATEGY_CONFIG.copy()
    config['initial_capital'] = args.capital
    config['commission_percent'] = args.commission
    config['sma_short'] = args.sma_short
    config['sma_long'] = args.sma_long
    
    if args.batch:
        results = []
        for symbol in args.batch:
            result = backtest_strategy(symbol, config)
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
        backtest_strategy(args.symbol, config)
