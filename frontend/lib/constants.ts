// Ticker-to-category mapping.
// SOT: must include every ticker in .github/workflows/update-signals.yml.
// Missing tickers fall through to '' in PageClient filter → hidden from UI.

export const TICKER_CATEGORY: Record<string, string> = {
  NVDA: '半導體', AMD: '半導體', ASML: '半導體', INTC: '半導體',
  TSM: '半導體', MU: '半導體', SNDK: '半導體', LWLG: '半導體', '2454.TW': '半導體',
  '2330.TW': '晶圓',
  LITE: '光電', '2308.TW': '電子',
  COHR: '雷射',
  GLW: '材料',
  GOOGL: 'AI/雲端', MSFT: 'AI/雲端', AMZN: 'AI/雲端', META: 'AI/雲端', PLTR: 'AI/雲端',
  INOD: 'AI資料',
  AAPL: '消費電子', DELL: '消費電子',
  CRWD: '資安', TSLA: 'EV', ONDS: '無人機',
  QUBT: '量子',
  RKLB: '太空', ASTS: '太空',
  'BTC-USD': '加密貨幣', 'ETH-USD': '加密貨幣',
  SPY: 'ETF', QQQ: 'ETF', SOXX: 'ETF', IBB: 'ETF',
  '0050.TW': '台股ETF',
  '^GSPC': '指數', '^VIX': '指數', '^TNX': '指數',
  NOK: '通訊', 'CL=F': '原物料',
};

export const NEWS_CATEGORIES = ['台股', '美股', '加密貨幣', '宏觀'] as const;

export const SIG_CATS = Array.from(new Set(Object.values(TICKER_CATEGORY))).sort();
