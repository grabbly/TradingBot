#!/usr/bin/env python3
"""
Simple Flask web app to display EMA charts from PostgreSQL
Runs on localhost:5001 (nginx will proxy treddy.acebox.eu to this port)
"""

import os
from flask import Flask, render_template, jsonify, send_file, request
from datetime import datetime, timedelta
import psycopg2
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Database config
DB_CONFIG = {
    'host': os.environ.get('PGHOST', 'localhost'),
    'port': int(os.environ.get('PGPORT', '5432')),
    'dbname': os.environ.get('PGDATABASE', 'trading_bot'),
    'user': os.environ.get('PGUSER', 'n8n_user'),
    'password': os.environ.get('PGPASSWORD', '***REMOVED***'),
}


def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data/<symbol>')
def get_data(symbol):
    days = int(request.args.get('days', 7))
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT timestamp, close_price, ema5, ema20, action, crossover
                FROM ema_snapshots
                WHERE symbol = %s
                  AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp
                """,
                (symbol.upper(), days),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    data = [
        {
            'timestamp': r[0].isoformat(),
            'close': float(r[1]) if r[1] else None,
            'ema5': float(r[2]) if r[2] else None,
            'ema20': float(r[3]) if r[3] else None,
            'action': r[4],
            'crossover': r[5],
        }
        for r in rows
    ]
    return jsonify(data)


@app.route('/chart/<symbol>.png')
def chart_png(symbol):
    from flask import request
    from datetime import datetime, timedelta
    
    days = int(request.args.get('days', 1))
    hours = request.args.get('hours', None)
    start_time = request.args.get('start_time', None)  # ISO format datetime
    
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if hours and start_time:
                # Load extra data for EMA warmup (1 day before)
                hours = int(hours)
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=hours)
                warmup_start_dt = start_dt - timedelta(days=1)
                
                cur.execute(
                    """
                    SELECT timestamp, close_price
                    FROM ema_snapshots
                    WHERE symbol = %s
                      AND timestamp >= %s
                      AND timestamp <= %s
                    ORDER BY timestamp
                    """,
                    (symbol.upper(), warmup_start_dt, end_dt),
                )
            else:
                # Show full days - load extra day for EMA warmup
                warmup_days = days + 1
                cur.execute(
                    """
                    SELECT timestamp, close_price
                    FROM ema_snapshots
                    WHERE symbol = %s
                      AND timestamp >= NOW() - INTERVAL '%s days'
                    ORDER BY timestamp
                    """,
                    (symbol.upper(), warmup_days),
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        # Return empty chart
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
        ax.set_title(f'{symbol.upper()} - No Data')
    else:
        timestamps = [r[0] for r in rows]
        close_prices = [float(r[1]) if r[1] else None for r in rows]
        
        # Calculate EMA5 and EMA50 dynamically on ALL data (including warmup)
        def calculate_ema(prices, period):
            # Filter out None values
            valid_prices = [p for p in prices if p is not None]
            if len(valid_prices) < period:
                return [None] * len(prices)
            
            ema = [None] * (period - 1)
            multiplier = 2 / (period + 1)
            sma = sum(valid_prices[:period]) / period
            ema.append(sma)
            for i in range(period, len(valid_prices)):
                ema_val = (valid_prices[i] - ema[-1]) * multiplier + ema[-1]
                ema.append(ema_val)
            
            # Pad to match original length if needed
            while len(ema) < len(prices):
                ema.append(None)
            
            return ema
        
        ema5 = calculate_ema(close_prices, 5)
        ema50 = calculate_ema(close_prices, 50)
        
        # Filter to display window only (exclude warmup period)
        if hours and start_time:
            display_start_idx = 0
            for i, ts in enumerate(timestamps):
                if ts >= start_dt:
                    display_start_idx = i
                    break
            
            timestamps = timestamps[display_start_idx:]
            close_prices = close_prices[display_start_idx:]
            ema5 = ema5[display_start_idx:]
            ema50 = ema50[display_start_idx:]
        else:
            # Filter to show only requested days (exclude warmup day)
            from datetime import datetime
            cutoff_time = datetime.now(timestamps[0].tzinfo) - timedelta(days=days)
            display_start_idx = 0
            for i, ts in enumerate(timestamps):
                if ts >= cutoff_time:
                    display_start_idx = i
                    break
            
            timestamps = timestamps[display_start_idx:]
            close_prices = close_prices[display_start_idx:]
            ema5 = ema5[display_start_idx:]
            ema50 = ema50[display_start_idx:]

        # Insert flat line for gaps > 1 hour (market close to open)
        from datetime import timedelta
        timestamps_clean = []
        close_prices_clean = []
        ema5_clean = []
        ema50_clean = []
        
        for i, ts in enumerate(timestamps):
            if i > 0:
                time_diff = (ts - timestamps[i-1]).total_seconds() / 60  # minutes
                if time_diff > 60:  # More than 1 hour gap
                    # Insert point at previous timestamp with previous values (flat line)
                    timestamps_clean.append(ts)
                    close_prices_clean.append(close_prices[i-1])
                    ema5_clean.append(ema5[i-1])
                    ema50_clean.append(ema50[i-1])
            
            timestamps_clean.append(ts)
            close_prices_clean.append(close_prices[i])
            ema5_clean.append(ema5[i])
            ema50_clean.append(ema50[i])

        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Thin smooth lines with breaks at market close/open
        ax.plot(timestamps_clean, close_prices_clean, label='Close', color='black', linewidth=0.75)
        ax.plot(timestamps_clean, ema5_clean, label='EMA 5', color='green', linewidth=0.5)
        ax.plot(timestamps_clean, ema50_clean, label='EMA 50', color='orange', linewidth=0.5)

        ax.set_title(f'{symbol.upper()} Price & EMA 5/50 (last {days} days)')
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format X-axis to show detailed time labels with minutes
        import matplotlib.dates as mdates
        
        # Adaptive time formatting based on data range
        if days <= 1:
            # For 1 day: show every 30 minutes
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30]))
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=10))
        elif days <= 5:
            # For 5 days: show every hour with minutes
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[0, 30]))
        else:
            # For more days: show every 4 hours
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        
        fig.autofmt_xdate()  # Rotate date labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=7)
        
        fig.tight_layout()

    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/load-historical', methods=['POST'])
def load_historical():
    """Endpoint to trigger historical data loading"""
    import subprocess
    from flask import request
    
    # Get parameters from request or use defaults
    data = request.get_json() if request.is_json else {}
    symbols = data.get('symbols', ['NVDA', 'AAPL', 'TSLA'])
    interval = data.get('interval', '5m')
    period = data.get('period', '7d')
    
    # Build command
    venv_python = '/home/gabby/TradingBot/web/venv/bin/python'
    script_path = '/home/gabby/TradingBot/web/load_historical_data.py'
    
    if isinstance(symbols, list):
        cmd = [venv_python, script_path, '--batch'] + symbols + ['--interval', interval, '--period', period]
    else:
        cmd = [venv_python, script_path, '--symbol', symbols, '--interval', interval, '--period', period]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return jsonify({
            'status': 'success',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Command timeout after 5 minutes'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/backtest')
def backtest_page():
    """Backtest form page"""
    return render_template('backtest.html')


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtest and return HTML results"""
    import subprocess
    from flask import request
    
    data = request.get_json() if request.is_json else {}
    symbols = data.get('symbols', ['NVDA'])
    capital = float(data.get('capital', 10000))
    commission = float(data.get('commission', 0.0))
    position_size = float(data.get('position_size', 100))
    confirmation = float(data.get('confirmation', 0.75))
    start_time = data.get('start_time')  # ISO format datetime (required)
    window_hours = data.get('window_hours')  # Number of hours (required)
    
    if not start_time or not window_hours:
        return jsonify({'status': 'error', 'message': 'Start time and window hours are required'}), 400
    
    venv_python = '/home/gabby/TradingBot/web/venv/bin/python'
    script_path = '/home/gabby/TradingBot/web/backtest_ema_strategy.py'
    
    if isinstance(symbols, list) and len(symbols) > 1:
        cmd = [venv_python, script_path, '--batch'] + symbols + [
            '--capital', str(capital),
            '--commission', str(commission),
            '--position-size', str(position_size),
            '--confirmation', str(confirmation),
            '--start-time', start_time,
            '--window-hours', str(window_hours)
        ]
    else:
        symbol = symbols[0] if isinstance(symbols, list) else symbols
        cmd = [venv_python, script_path,
            '--symbol', symbol,
            '--capital', str(capital),
            '--commission', str(commission),
            '--position-size', str(position_size),
            '--confirmation', str(confirmation),
            '--start-time', start_time,
            '--window-hours', str(window_hours)
        ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Parse results from stdout
        output = result.stdout
        
        return jsonify({
            'status': 'success',
            'output': output,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Backtest timeout after 5 minutes'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
