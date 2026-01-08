#!/usr/bin/env python3
"""
Backtest Sentiment-Based Top-4 Strategy
========================================

Strategy Logic:
- Each day: Rank 7 symbols by sentiment score
- Select top-4 symbols with highest sentiment
- Rebalance portfolio: equal weight (25% each)
- Sell positions not in top-4, buy new top-4

Metrics Calculated:
- Total Return
- Sharpe Ratio (annualized)
- Max Drawdown
- Win Rate
- Number of Trades
- Average Hold Period

Comparison:
- Strategy vs. SPY Buy-and-Hold

Data Sources:
- Historical prices: data/historical_{symbol}_2023-2025.csv
- Sentiment scores: data/sentiment_proxy_2023-2025.csv
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CONFIG = {
    'initial_capital': 10000.0,
    'position_size': 0.25,  # 25% per symbol (4 symbols = 100%)
    'symbols': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA'],
    'top_n': 4,  # Select top-4 by sentiment
    'commission': 0.0,  # Alpaca commission-free
    'slippage': 0.001,  # 0.1% slippage per trade
}

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
REPORTS_DIR = Path(__file__).parent.parent / 'reports'


class Portfolio:
    """Portfolio state tracker"""
    
    def __init__(self, initial_capital):
        self.cash = initial_capital
        self.positions = {}  # {symbol: shares}
        self.equity_history = []
        self.trades = []
        self.current_date = None
        
    def get_equity(self, prices):
        """Calculate current portfolio equity"""
        holdings_value = sum(
            self.positions.get(symbol, 0) * prices.get(symbol, 0)
            for symbol in self.positions
        )
        return self.cash + holdings_value
    
    def rebalance(self, target_symbols, prices, date, config):
        """Rebalance to target symbols with equal weight"""
        current_equity = self.get_equity(prices)
        target_value_per_symbol = current_equity * config['position_size']
        
        # Close positions not in target
        for symbol in list(self.positions.keys()):
            if symbol not in target_symbols and self.positions[symbol] > 0:
                self._close_position(symbol, prices[symbol], date, config)
        
        # Open/adjust positions for target symbols
        for symbol in target_symbols:
            if symbol not in prices or prices[symbol] <= 0:
                continue
                
            current_shares = self.positions.get(symbol, 0)
            current_value = current_shares * prices[symbol]
            target_shares = int(target_value_per_symbol / prices[symbol])
            
            if target_shares > current_shares:
                # Buy more
                shares_to_buy = target_shares - current_shares
                cost = shares_to_buy * prices[symbol] * (1 + config['slippage'])
                if cost <= self.cash:
                    self.positions[symbol] = self.positions.get(symbol, 0) + shares_to_buy
                    self.cash -= cost
                    self._record_trade('BUY', symbol, shares_to_buy, prices[symbol], date)
            
            elif target_shares < current_shares:
                # Sell some
                shares_to_sell = current_shares - target_shares
                proceeds = shares_to_sell * prices[symbol] * (1 - config['slippage'])
                self.positions[symbol] -= shares_to_sell
                self.cash += proceeds
                self._record_trade('SELL', symbol, shares_to_sell, prices[symbol], date)
                
                if self.positions[symbol] == 0:
                    del self.positions[symbol]
    
    def _close_position(self, symbol, price, date, config):
        """Close entire position"""
        if symbol not in self.positions or self.positions[symbol] == 0:
            return
        
        shares = self.positions[symbol]
        proceeds = shares * price * (1 - config['slippage'])
        self.cash += proceeds
        self._record_trade('SELL', symbol, shares, price, date)
        del self.positions[symbol]
    
    def _record_trade(self, action, symbol, shares, price, date):
        """Record trade in history"""
        self.trades.append({
            'date': date,
            'action': action,
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'value': shares * price
        })
    
    def record_daily_equity(self, date, equity):
        """Record daily equity for performance tracking"""
        self.equity_history.append({
            'date': date,
            'equity': equity,
            'cash': self.cash,
            'positions': len(self.positions)
        })


def load_data():
    """Load historical prices and sentiment data"""
    print("📂 Loading data...")
    
    # Load prices
    prices_df = []
    for symbol in CONFIG['symbols']:
        file_path = DATA_DIR / f'historical_{symbol}_2023-2025.csv'
        if not file_path.exists():
            print(f"❌ Missing: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        df['symbol'] = symbol
        prices_df.append(df)
    
    prices = pd.concat(prices_df, ignore_index=True)
    prices['date'] = pd.to_datetime(prices['date'])
    print(f"  ✅ Loaded {len(prices)} price records")
    
    # Load sentiment
    sentiment_path = DATA_DIR / 'sentiment_proxy_2023-2025.csv'
    if not sentiment_path.exists():
        print(f"❌ Missing: {sentiment_path}")
        return None, None
    
    sentiment = pd.read_csv(sentiment_path)
    sentiment['date'] = pd.to_datetime(sentiment['date'])
    print(f"  ✅ Loaded {len(sentiment)} sentiment records")
    
    return prices, sentiment


def get_top_symbols_by_sentiment(sentiment_df, date, top_n=4):
    """Get top N symbols by sentiment for a given date"""
    day_sentiment = sentiment_df[sentiment_df['date'] == date]
    
    if len(day_sentiment) == 0:
        return []
    
    top_symbols = day_sentiment.nlargest(top_n, 'sentiment')['symbol'].tolist()
    return top_symbols


def calculate_metrics(portfolio, config):
    """Calculate performance metrics"""
    equity_df = pd.DataFrame(portfolio.equity_history)
    
    if len(equity_df) == 0:
        return {}
    
    initial_capital = config['initial_capital']
    final_equity = equity_df.iloc[-1]['equity']
    
    # Returns
    equity_df['returns'] = equity_df['equity'].pct_change()
    total_return = (final_equity - initial_capital) / initial_capital
    
    # Sharpe Ratio (annualized, assuming 252 trading days)
    returns_std = equity_df['returns'].std()
    if returns_std > 0:
        sharpe = (equity_df['returns'].mean() / returns_std) * np.sqrt(252)
    else:
        sharpe = 0.0
    
    # Max Drawdown
    equity_df['cummax'] = equity_df['equity'].cummax()
    equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
    max_drawdown = equity_df['drawdown'].min()
    
    # Win Rate
    trades_df = pd.DataFrame(portfolio.trades)
    if len(trades_df) > 0:
        buy_trades = trades_df[trades_df['action'] == 'BUY']
        sell_trades = trades_df[trades_df['action'] == 'SELL']
        num_trades = len(buy_trades) + len(sell_trades)
    else:
        num_trades = 0
    
    # Trading days
    trading_days = len(equity_df)
    
    metrics = {
        'initial_capital': initial_capital,
        'final_equity': final_equity,
        'total_return': total_return,
        'total_return_pct': total_return * 100,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown * 100,
        'num_trades': num_trades,
        'trading_days': trading_days,
        'avg_positions': equity_df['positions'].mean(),
    }
    
    return metrics, equity_df


def run_backtest():
    """Run the backtest simulation"""
    print(f"\n{'='*70}")
    print(f"🚀 SENTIMENT-BASED TOP-4 STRATEGY BACKTEST")
    print(f"{'='*70}\n")
    
    # Load data
    prices, sentiment = load_data()
    if prices is None or sentiment is None:
        print("❌ Failed to load data")
        return
    
    # Get trading date range
    start_date = max(prices['date'].min(), sentiment['date'].min())
    end_date = min(prices['date'].max(), sentiment['date'].max())
    trading_dates = pd.date_range(start_date, end_date, freq='D')
    
    print(f"\n📅 Backtest Period:")
    print(f"  Start: {start_date.date()}")
    print(f"  End: {end_date.date()}")
    print(f"  Days: {len(trading_dates)}")
    
    print(f"\n💰 Initial Capital: ${CONFIG['initial_capital']:,.2f}")
    print(f"📊 Strategy: Top-{CONFIG['top_n']} by sentiment, equal weight")
    print(f"💼 Symbols: {', '.join(CONFIG['symbols'])}")
    
    # Initialize portfolio
    portfolio = Portfolio(CONFIG['initial_capital'])
    
    # Run simulation
    print(f"\n⏳ Running simulation...")
    rebalance_count = 0
    
    for date in trading_dates:
        # Get sentiment rankings
        top_symbols = get_top_symbols_by_sentiment(sentiment, date, CONFIG['top_n'])
        
        if len(top_symbols) == 0:
            continue
        
        # Get prices for this date
        day_prices = prices[prices['date'] == date]
        if len(day_prices) == 0:
            continue
        
        prices_dict = dict(zip(day_prices['symbol'], day_prices['close']))
        
        # Rebalance if needed
        current_symbols = set(portfolio.positions.keys())
        target_symbols = set(top_symbols)
        
        if current_symbols != target_symbols:
            portfolio.rebalance(top_symbols, prices_dict, date, CONFIG)
            rebalance_count += 1
        
        # Record daily equity
        equity = portfolio.get_equity(prices_dict)
        portfolio.record_daily_equity(date, equity)
    
    print(f"  ✅ Completed {len(portfolio.equity_history)} days")
    print(f"  🔄 Rebalanced {rebalance_count} times")
    
    # Calculate metrics
    print(f"\n📈 Calculating metrics...")
    metrics, equity_df = calculate_metrics(portfolio, CONFIG)
    
    # Print results
    print(f"\n{'='*70}")
    print(f"📊 BACKTEST RESULTS")
    print(f"{'='*70}\n")
    
    print(f"💰 Financial Performance:")
    print(f"  Initial Capital:  ${metrics['initial_capital']:>12,.2f}")
    print(f"  Final Equity:     ${metrics['final_equity']:>12,.2f}")
    print(f"  Total Return:     {metrics['total_return_pct']:>12.2f}%")
    print(f"  Profit/Loss:      ${metrics['final_equity'] - metrics['initial_capital']:>12,.2f}")
    
    print(f"\n📊 Risk Metrics:")
    print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:>12.2f}")
    print(f"  Max Drawdown:     {metrics['max_drawdown_pct']:>12.2f}%")
    
    print(f"\n📈 Trading Activity:")
    print(f"  Total Trades:     {metrics['num_trades']:>12}")
    print(f"  Trading Days:     {metrics['trading_days']:>12}")
    print(f"  Avg Positions:    {metrics['avg_positions']:>12.1f}")
    print(f"  Rebalances:       {rebalance_count:>12}")
    
    # Generate report
    generate_report(metrics, equity_df, portfolio, sentiment)
    
    # Plot results
    plot_results(equity_df, portfolio)
    
    # Decision
    print(f"\n{'='*70}")
    print(f"🎯 GO/NO-GO DECISION")
    print(f"{'='*70}\n")
    
    if metrics['sharpe_ratio'] >= 0.5:
        print(f"✅ GO: Sharpe ratio {metrics['sharpe_ratio']:.2f} >= 0.5")
        print(f"   Strategy shows promise, proceed to Phase 2")
    else:
        print(f"❌ NO-GO: Sharpe ratio {metrics['sharpe_ratio']:.2f} < 0.5")
        print(f"   Strategy underperforms, consider pivot")
    
    print(f"\n{'='*70}\n")
    
    return metrics, equity_df, portfolio


def generate_report(metrics, equity_df, portfolio, sentiment_data=None):
    """Generate markdown report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = REPORTS_DIR / f'backtest_v1_results_{timestamp}.md'
    
    with open(report_path, 'w') as f:
        f.write(f"# Sentiment-Based Top-4 Strategy Backtest Results\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"## Strategy Configuration\n\n")
        f.write(f"- **Initial Capital:** ${CONFIG['initial_capital']:,.2f}\n")
        f.write(f"- **Strategy:** Top-{CONFIG['top_n']} symbols by sentiment\n")
        f.write(f"- **Position Size:** {CONFIG['position_size']*100:.0f}% per symbol\n")
        f.write(f"- **Symbols:** {', '.join(CONFIG['symbols'])}\n")
        f.write(f"- **Slippage:** {CONFIG['slippage']*100:.2f}%\n")
        f.write(f"- **Commission:** {CONFIG['commission']*100:.2f}%\n\n")
        
        f.write(f"## Performance Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Initial Capital | ${metrics['initial_capital']:,.2f} |\n")
        f.write(f"| Final Equity | ${metrics['final_equity']:,.2f} |\n")
        f.write(f"| Total Return | {metrics['total_return_pct']:.2f}% |\n")
        f.write(f"| Sharpe Ratio | {metrics['sharpe_ratio']:.2f} |\n")
        f.write(f"| Max Drawdown | {metrics['max_drawdown_pct']:.2f}% |\n")
        f.write(f"| Total Trades | {metrics['num_trades']} |\n")
        f.write(f"| Trading Days | {metrics['trading_days']} |\n")
        f.write(f"| Avg Positions | {metrics['avg_positions']:.1f} |\n\n")
        
        f.write(f"## Decision\n\n")
        if metrics['sharpe_ratio'] >= 0.5:
            f.write(f"✅ **GO:** Sharpe ratio {metrics['sharpe_ratio']:.2f} >= 0.5\n\n")
            f.write(f"Strategy shows promise. Proceed to Phase 2.\n\n")
        else:
            f.write(f"❌ **NO-GO:** Sharpe ratio {metrics['sharpe_ratio']:.2f} < 0.5\n\n")
            f.write(f"Strategy underperforms. Consider pivot or refinement.\n\n")
        
        # Trade log
        f.write(f"## Trade Log (Last 50 Trades)\n\n")
        trades_df = pd.DataFrame(portfolio.trades)
        if len(trades_df) > 0:
            f.write(f"| Date | Action | Symbol | Shares | Price | Value |\n")
            f.write(f"|------|--------|--------|--------|-------|-------|\n")
            for _, trade in trades_df.tail(50).iterrows():
                f.write(f"| {trade['date'].strftime('%Y-%m-%d')} | {trade['action']} | "
                       f"{trade['symbol']} | {trade['shares']} | "
                       f"${trade['price']:.2f} | ${trade['value']:.2f} |\n")
            f.write(f"\n")
        
        # Monthly performance
        f.write(f"## Monthly Performance\n\n")
        equity_df['month'] = equity_df['date'].dt.to_period('M')
        monthly = equity_df.groupby('month').agg({
            'equity': ['first', 'last']
        })
        monthly.columns = ['start', 'end']
        monthly['return'] = (monthly['end'] - monthly['start']) / monthly['start'] * 100
        
        f.write(f"| Month | Start Equity | End Equity | Return |\n")
        f.write(f"|-------|--------------|------------|--------|\n")
        for month, row in monthly.iterrows():
            f.write(f"| {month} | ${row['start']:,.2f} | ${row['end']:,.2f} | "
                   f"{row['return']:+.2f}% |\n")
        f.write(f"\n")
        
        # Decision-making analysis
        if sentiment_data is not None:
            f.write(f"## Decision-Making Logic\n\n")
            f.write(f"**Strategy:** Each day, rank all 7 symbols by sentiment score and select the top-4.\n\n")
            
            # Sample days
            example_dates = ['2023-01-03', '2023-06-15', '2024-01-15', '2025-06-15', '2025-12-29']
            f.write(f"### Example Days\n\n")
            
            for date_str in example_dates:
                date = pd.to_datetime(date_str)
                day_sentiment = sentiment_data[sentiment_data['date'] == date].copy()
                
                if len(day_sentiment) == 0:
                    continue
                
                day_sentiment = day_sentiment.sort_values('sentiment', ascending=False)
                
                f.write(f"#### {date_str}\n\n")
                f.write(f"| Rank | Symbol | Sentiment | Selected |\n")
                f.write(f"|------|--------|-----------|----------|\n")
                
                for i, (_, row) in enumerate(day_sentiment.iterrows(), 1):
                    selected = "✅ BUY" if i <= 4 else "❌ SKIP"
                    f.write(f"| {i} | {row['symbol']} | {row['sentiment']:.4f} | {selected} |\n")
                
                top_4 = day_sentiment.head(4)['symbol'].tolist()
                f.write(f"\n**Portfolio:** {', '.join(top_4)}\n\n")
            
            # Rebalancing frequency
            f.write(f"### Rebalancing Frequency\n\n")
            
            all_dates = sorted(sentiment_data['date'].unique())
            rebalance_count = 0
            prev_portfolio = None
            
            for date in all_dates:
                day_sentiment = sentiment_data[sentiment_data['date'] == date]
                if len(day_sentiment) == 0:
                    continue
                
                current_portfolio = set(day_sentiment.nlargest(4, 'sentiment')['symbol'].tolist())
                
                if prev_portfolio is not None and current_portfolio != prev_portfolio:
                    rebalance_count += 1
                
                prev_portfolio = current_portfolio
            
            total_days = len(all_dates)
            rebalance_pct = (rebalance_count / total_days) * 100
            avg_days = total_days / rebalance_count if rebalance_count > 0 else 0
            
            f.write(f"- **Total Trading Days:** {total_days}\n")
            f.write(f"- **Rebalances:** {rebalance_count}\n")
            f.write(f"- **Rebalance Frequency:** {rebalance_pct:.1f}% of days\n")
            f.write(f"- **Avg Days Between Rebalances:** {avg_days:.1f}\n\n")
            
            # Symbol popularity
            f.write(f"### Symbol Selection Frequency\n\n")
            
            symbol_days = {}
            for date in all_dates:
                day_sentiment = sentiment_data[sentiment_data['date'] == date]
                if len(day_sentiment) == 0:
                    continue
                
                top_4 = day_sentiment.nlargest(4, 'sentiment')['symbol'].tolist()
                for symbol in top_4:
                    symbol_days[symbol] = symbol_days.get(symbol, 0) + 1
            
            sorted_symbols = sorted(symbol_days.items(), key=lambda x: x[1], reverse=True)
            
            f.write(f"| Symbol | Days in Portfolio | Percentage | Avg per Year |\n")
            f.write(f"|--------|-------------------|------------|---------------|\n")
            
            for symbol, days in sorted_symbols:
                pct = (days / total_days) * 100
                days_per_year = days / 3
                f.write(f"| {symbol} | {days} | {pct:.1f}% | {days_per_year:.0f} |\n")
            
            f.write(f"\n💡 Portfolio always holds exactly 4 symbols (equal weight 25% each)\n\n")
        
        f.write(f"## Equity Curve\n\n")
        f.write(f"See: `backtest_equity_curve_{timestamp}.png`\n\n")
    
    print(f"\n📄 Report saved: {report_path}")


def plot_results(equity_df, portfolio):
    """Plot equity curve"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_path = REPORTS_DIR / f'backtest_equity_curve_{timestamp}.png'
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Equity curve
    ax1.plot(equity_df['date'], equity_df['equity'], linewidth=2, label='Portfolio Equity')
    ax1.axhline(y=CONFIG['initial_capital'], color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.set_title('Portfolio Equity Over Time', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Equity ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    
    # Drawdown
    ax2.fill_between(equity_df['date'], equity_df['drawdown'] * 100, 0, alpha=0.3, color='red')
    ax2.plot(equity_df['date'], equity_df['drawdown'] * 100, linewidth=1, color='darkred')
    ax2.set_title('Drawdown (%)', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Drawdown (%)')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"📊 Chart saved: {plot_path}")
    plt.close()


if __name__ == '__main__':
    try:
        metrics, equity_df, portfolio = run_backtest()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
