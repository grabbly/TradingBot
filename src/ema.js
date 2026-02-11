/**
 * EMA (Exponential Moving Average) Calculator
 * For use in n8n Function Node
 */

/**
 * Calculates EMA for an array of prices
 * @param {number[]} prices - Array of closing prices (from old to new)
 * @param {number} period - EMA period
 * @returns {number[]} - Array of EMA values
 */
function calculateEMA(prices, period) {
  if (prices.length < period) {
    throw new Error(`Insufficient data: need at least ${period} candles`);
  }

  const ema = [];
  const multiplier = 2 / (period + 1);

  // First EMA value = SMA for first N periods
  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += prices[i];
  }
  ema[period - 1] = sum / period;

  // Remaining EMA values
  for (let i = period; i < prices.length; i++) {
    ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1];
  }

  return ema;
}

/**
 * Calculates current EMA 5 and EMA 20 values
 * @param {Object[]} bars - OHLC data from Alpaca
 * @returns {Object} - Current and previous EMA values
 */
function calculateDualEMA(bars) {
  // Extract closing prices
  const closes = bars.map(bar => parseFloat(bar.c));
  
  const ema5 = calculateEMA(closes, 5);
  const ema20 = calculateEMA(closes, 20);
  
  const lastIndex = closes.length - 1;
  const prevIndex = closes.length - 2;
  
  return {
    current: {
      ema5: ema5[lastIndex],
      ema20: ema20[lastIndex],
      close: closes[lastIndex],
      timestamp: bars[lastIndex].t
    },
    previous: {
      ema5: ema5[prevIndex],
      ema20: ema20[prevIndex],
      close: closes[prevIndex],
      timestamp: bars[prevIndex].t
    }
  };
}

/**
 * Рассчитывает все EMA периоды для бара
 * @param {Object[]} bars - OHLC данные от Alpaca
 * @param {number[]} periods - Массив периодов EMA [5, 8, 9, 13, 20, 21, 34, 50, 100, 200]
 * @returns {Object} - Текущие и предыдущие значения всех EMA
 */
function calculateMultipleEMA(bars, periods = [5, 8, 9, 13, 20, 21, 34, 50, 100, 200]) {
  const closes = bars.map(bar => parseFloat(bar.c));
  const lastIndex = closes.length - 1;
  const prevIndex = closes.length - 2;
  
  const current = {
    close: closes[lastIndex],
    timestamp: bars[lastIndex].t
  };
  
  const previous = {
    close: closes[prevIndex],
    timestamp: bars[prevIndex].t
  };
  
  // Рассчитываем EMA для каждого периода
  periods.forEach(period => {
    if (closes.length >= period) {
      const ema = calculateEMA(closes, period);
      current[`ema${period}`] = ema[lastIndex];
      previous[`ema${period}`] = ema[prevIndex];
    } else {
      current[`ema${period}`] = null;
      previous[`ema${period}`] = null;
    }
  });
  
  return { current, previous, periods };
}

// Экспорт для n8n (копировать в Function Node)
// return { json: calculateDualEMA($input.first().json.bars) };
// return { json: calculateMultipleEMA($input.first().json.bars) };

module.exports = { calculateEMA, calculateDualEMA, calculateMultipleEMA };
