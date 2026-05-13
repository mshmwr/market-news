'use client';

import { useState } from 'react';

type Status = 'idle' | 'pending' | 'triggered' | 'running' | 'cooldown' | 'error';

function formatTw(iso: string): string {
  return new Date(iso).toLocaleString('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function RefreshButton() {
  const [status, setStatus] = useState<Status>('idle');
  const [message, setMessage] = useState<string>('');

  async function handleClick() {
    setStatus('pending');
    setMessage('');
    try {
      const res = await fetch('/api/signals/refresh', { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        setStatus('triggered');
        return;
      }
      if (data.code === 'running') {
        setStatus('running');
        setMessage(data.error);
        return;
      }
      if (data.code === 'cooldown') {
        setStatus('cooldown');
        setMessage(`下次可觸發時間：${formatTw(data.nextAvailable)}`);
        return;
      }
      setStatus('error');
      setMessage(data.error || `HTTP ${res.status}`);
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : String(e));
    }
  }

  const disabled =
    status === 'pending' || status === 'triggered' || status === 'running' || status === 'cooldown';

  let label = '🔄 重新計算 / Refresh';
  if (status === 'pending') label = '觸發中… / Triggering…';
  else if (status === 'triggered') label = '✓ 已觸發，約 5–10 分鐘後重新整理頁面';
  else if (status === 'running') label = '⏳ 任務執行中 / Run in progress';
  else if (status === 'cooldown') label = '⏸ 6 小時內已觸發過 / Cooled down';
  else if (status === 'error') label = '⚠ 觸發失敗，再試一次';

  const subText =
    status === 'error' || status === 'running' || status === 'cooldown' ? message : '';

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
      {subText && (
        <span
          className={`text-[11px] ${
            status === 'error' ? 'text-red-600' : 'text-gray-500'
          }`}
        >
          {subText}
        </span>
      )}
      <span className="text-[11px] text-gray-400">
        固定排程：每天 04:00（台灣時間）
      </span>
    </div>
  );
}
