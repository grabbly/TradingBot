/**
 * Signal Detection - Crossover и подтверждение
 * Для использования в n8n Function Node
 */

/**
 * Состояние бота (хранится в n8n Static Data)
 * @typedef {Object} BotState
 * @property {string} status - 'flat' | 'waiting_confirmation' | 'in_position'
 * @property {number|null} crossoverPrice - Цена на момент bullish crossover
 * @property {string|null} crossoverTime - Время crossover
 * @property {number|null} entryPrice - Цена входа в позицию
 * @property {string|null} entryTime - Время входа
 */

/**
 * Определяет тип crossover
 * @param {Object} current - Текущие значения EMA
 * @param {Object} previous - Предыдущие значения EMA
 * @returns {string} - 'bullish' | 'bearish' | 'none'
 */
function detectCrossover(current, previous) {
  const wasBelowOrEqual = previous.ema5 <= previous.ema20;
  const isAbove = current.ema5 > current.ema20;
  
  const wasAboveOrEqual = previous.ema5 >= previous.ema20;
  const isBelow = current.ema5 < current.ema20;
  
  if (wasBelowOrEqual && isAbove) {
    return 'bullish';
  }
  
  if (wasAboveOrEqual && isBelow) {
    return 'bearish';
  }
  
  return 'none';
}

/**
 * Основная логика принятия решений
 * @param {Object} emaData - Данные EMA (current, previous)
 * @param {Object} state - Текущее состояние бота
 * @param {number} confirmationPercent - Процент подтверждения (например, 0.75)
 * @param {number} currentPrice - Текущая цена (last trade или close)
 * @returns {Object} - { action, newState, details }
 */
function processSignal(emaData, state, confirmationPercent, currentPrice) {
  const crossover = detectCrossover(emaData.current, emaData.previous);
  
  let action = 'hold';
  let newState = { ...state };
  let details = {
    crossover,
    ema5: emaData.current.ema5,
    ema20: emaData.current.ema20,
    currentPrice,
    timestamp: emaData.current.timestamp
  };
  
  // Логика по состояниям
  switch (state.status) {
    
    case 'flat':
      if (crossover === 'bullish') {
        // Зафиксировали bullish crossover — ждём подтверждения
        newState = {
          status: 'waiting_confirmation',
          crossoverPrice: emaData.current.close,
          crossoverTime: emaData.current.timestamp,
          entryPrice: null,
          entryTime: null
        };
        action = 'signal_detected';
        details.message = `Bullish crossover detected at ${emaData.current.close}. Waiting for +${confirmationPercent}% confirmation.`;
      }
      break;
      
    case 'waiting_confirmation':
      const targetPrice = state.crossoverPrice * (1 + confirmationPercent / 100);
      
      if (crossover === 'bearish') {
        // Bearish crossover — отменяем сигнал
        newState = {
          status: 'flat',
          crossoverPrice: null,
          crossoverTime: null,
          entryPrice: null,
          entryTime: null
        };
        action = 'signal_cancelled';
        details.message = 'Bearish crossover appeared. Signal cancelled.';
        
      } else if (currentPrice >= targetPrice) {
        // Цена достигла уровня подтверждения — BUY
        newState = {
          status: 'in_position',
          crossoverPrice: state.crossoverPrice,
          crossoverTime: state.crossoverTime,
          entryPrice: currentPrice,
          entryTime: new Date().toISOString()
        };
        action = 'buy';
        details.message = `Price confirmed at ${currentPrice} (target was ${targetPrice.toFixed(2)}). Opening long position.`;
        details.targetPrice = targetPrice;
        
      } else {
        details.message = `Waiting for confirmation. Current: ${currentPrice}, Target: ${targetPrice.toFixed(2)}`;
        details.targetPrice = targetPrice;
        details.remainingPercent = ((targetPrice - currentPrice) / currentPrice * 100).toFixed(3);
      }
      break;
      
    case 'in_position':
      if (crossover === 'bearish') {
        // Bearish crossover — закрываем позицию
        const profit = ((currentPrice - state.entryPrice) / state.entryPrice * 100).toFixed(2);
        
        newState = {
          status: 'flat',
          crossoverPrice: null,
          crossoverTime: null,
          entryPrice: null,
          entryTime: null
        };
        action = 'sell';
        details.message = `Bearish crossover detected. Closing position at ${currentPrice}. P/L: ${profit}%`;
        details.entryPrice = state.entryPrice;
        details.profitPercent = parseFloat(profit);
      }
      break;
  }
  
  return { action, newState, details };
}

/**
 * Рассчитывает уровень стоп-лосса
 * @param {number} entryPrice - Цена входа
 * @param {number} ema20 - Текущее значение EMA 20
 * @param {number} stopLossPercent - Процент стоп-лосса
 * @returns {number} - Цена стоп-лосса
 */
function calculateStopLoss(entryPrice, ema20, stopLossPercent) {
  const percentStop = entryPrice * (1 - stopLossPercent / 100);
  const emaStop = ema20 * 0.995; // Чуть ниже EMA 20
  
  // Берём более высокий стоп (более консервативный)
  return Math.max(percentStop, emaStop);
}

// Экспорт для n8n
module.exports = { detectCrossover, processSignal, calculateStopLoss };
