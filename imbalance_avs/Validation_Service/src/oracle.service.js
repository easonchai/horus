require('dotenv').config();
const axios = require("axios");

async function getPrice(pair) {
  // Extract symbol and quote from pair (e.g., "BTC/USDT" -> symbol="BTC", quote="USDT")
  let symbol, quote;
  
  // Split by forward slash
  if (pair.includes('/')) {
    const parts = pair.split('/');
    symbol = parts[0];
    quote = parts[1];
  } else {
    // Fallback for legacy format without slash
    // Common patterns like BTCUSDT, ETHUSDT, etc.
    if (pair.endsWith('USDT')) {
      symbol = pair.substring(0, pair.length - 4);
      quote = 'USDT';
    } else if (pair.endsWith('USD')) {
      symbol = pair.substring(0, pair.length - 3);
      quote = 'USD';
    } else if (pair.endsWith('BTC')) {
      symbol = pair.substring(0, pair.length - 3);
      quote = 'BTC';
    } else {
      // Default fallback - try to split at a reasonable point
      symbol = pair.substring(0, pair.length / 2);
      quote = pair.substring(pair.length / 2);
    }
  }

  try {
    const apiKey = process.env.COINMARKETCAP_API_KEY;
    
    if (!apiKey) {
      throw new Error('COINMARKETCAP_API_KEY is not defined in environment variables');
    }

    const response = await axios.get('https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest', {
      headers: {
        'X-CMC_PRO_API_KEY': apiKey
      },
      params: {
        symbol: symbol,
        convert: quote
      }
    });

    // Extract the price data
    const data = response.data.data;
    const symbolData = data[symbol][0];
    const price = symbolData.quote[quote].price;

    // Return in a format similar to Binance API response
    return {
      symbol: pair,
      price: price.toString()
    };
  } catch (err) {
    console.error('Error fetching price from CoinMarketCap:', err.message);
    throw err;
  }
}

module.exports = {
  getPrice,
}
