// MN-004: TypeScript interfaces derived from confirmed live signals.json and news.json schemas.

export type SignalAction = 'BUY' | 'HOLD' | 'SELL';

export interface TechnicalData {
  rsi?: number;
  macd_line?: number;
  macd_signal?: number;
  macd_histogram?: number;
  ma50?: number;
  volume_ratio?: number;
}

export interface FundamentalsData {
  pe_ratio?: number;
  forward_pe?: number;
  price_to_book?: number;
  revenue_growth?: number;
  profit_margin?: number;
  debt_to_equity?: number;
  target_mean_price?: number;
  current_price?: number;
  fifty_two_week_low?: number;
  fifty_two_week_high?: number;
  trailing_eps?: number;
  book_value?: number;
  peg_ratio?: number;
  short_name?: string;
  recommendation_key?: string;
  number_of_analyst_opinions?: number;
  sector?: string;
}

export interface UndervaluationData {
  upside_pct?: number;
  week52_position_pct?: number;
  graham_number?: number;
  price_vs_graham_pct?: number;
  relative_pe?: number;
  sector_pe_avg?: number;
  peg_ratio?: number;
}

export interface SourceItem {
  title?: string;
  url: string;
  published_ts?: number;
}

export interface SocialPost {
  title?: string;
  url: string;
}

export interface SignalResult {
  ticker: string;
  name?: string;
  signal: SignalAction;
  confidence: number;
  rationale: string;
  bull_case?: string;
  bear_case?: string;
  sources?: SourceItem[];
  social_posts?: SocialPost[];
  technical_data?: TechnicalData;
  fundamentals_data?: FundamentalsData;
  undervaluation_data?: UndervaluationData;
}

export interface SignalsResponse {
  generated_at: string;
  signals: SignalResult[];
}

export type NewsCategory = '台股' | '美股' | '加密貨幣' | '宏觀';

export interface NewsItem {
  title: string;
  description?: string;
  link: string;
  source: string;
  category: NewsCategory;
  published_ts: number;
}
