'use client';

import { useState } from 'react';

type Status = 'idle' | 'pending' | 'triggered' | 'error';

export default function RegenerateButton() {
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string>('');

  async function handleClick() {
    setStatus('pending');
    setError('');
    try {
      const res = await fetch('/api/digest/regenerate', { method: 'POST' });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setStatus('error');
        setError(data.error || `HTTP ${res.status}`);
        return;
      }
      setStatus('triggered');
    } catch (e) {
      setStatus('error');
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const disabled = status === 'pending' || status === 'triggered';

  let label = '🔄 重新產生 / Regenerate';
  if (status === 'pending') label = '觸發中… / Triggering…';
  else if (status === 'triggered') label = '✓ 已觸發，約 2–3 分鐘後重新整理頁面';
  else if (status === 'error') label = '⚠ 觸發失敗，再試一次';

  return (
    <div className="mb-3 flex flex-col gap-1">
      <button
        onClick={handleClick}
        disabled={disabled}
        className={`self-start px-3.5 py-1 rounded-full border text-[13px] cursor-pointer transition-all ${
          disabled
            ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
            : 'bg-white text-gray-700 border-gray-300 hover:border-gray-500'
        }`}
      >
        {label}
      </button>
      {status === 'error' && (
        <span className="text-[11px] text-red-600">{error}</span>
      )}
    </div>
  );
}
