/**
 * EMA (Exponential Moving Average) Calculator
 * Для использования в n8n Function Node
 */

/**
 * Рассчитывает EMA для массива цен
 * @param {number[]} prices - Массив цен закрытия (от старых к новым)
 * @param {number} period - Период EMA
 * @returns {number[]} - Массив значений EMA
 */
function calculateEMA(prices, period) {
  if (prices.length < period) {
    throw new Error(`Недостаточно данных: нужно минимум ${period} свечей`);
  }

  const ema = [];
  const multiplier = 2 / (period + 1);

  // Первое значение EMA = SMA за первые N периодов
  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += prices[i];
  }
  ema[period - 1] = sum / period;

  // Остальные значения EMA
  for (let i = period; i < prices.length; i++) {
    ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1];
  }

  return ema;
}

/**
 * Рассчитывает текущие значения EMA 5 и EMA 20
 * @param {Object[]} bars - OHLC данные от Alpaca
 * @returns {Object} - Текущие и предыдущие значения EMA
 */
function calculateDualEMA(bars) {
  // Извлекаем цены закрытия
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

// Экспорт для n8n (копировать в Function Node)
// return { json: calculateDualEMA($input.first().json.bars) };

module.exports = { calculateEMA, calculateDualEMA };
