'use client';

// Floating feedback button + modal — ported from legacy docs/index.html.
// Writes to Firestore `feedback` collection (ai-novel-generator-ng project).

import { useState } from 'react';

export default function FeedbackButton() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  function close() {
    setOpen(false);
    setText('');
  }

  async function submit() {
    const msg = text.trim();
    if (!msg) return;
    setSubmitting(true);
    try {
      const [{ addDoc, collection, serverTimestamp }, { getDb }] = await Promise.all([
        import('firebase/firestore'),
        import('@/lib/firebase'),
      ]);
      await addDoc(collection(getDb(), 'feedback'), {
        source: 'market-news',
        message: msg,
        created_at: serverTimestamp(),
        url: typeof window !== 'undefined' ? window.location.href : '',
      });
      close();
      setToast('建議已送出，謝謝！');
      setTimeout(() => setToast(null), 2500);
    } catch (err) {
      alert('送出失敗：' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-30 px-4 py-2 rounded-full bg-[#1d1d1f] text-white text-[13px] shadow-lg hover:bg-[#3a3a3c]"
      >
        💬 建議
      </button>

      {open && (
        <div
          onClick={(e) => { if (e.target === e.currentTarget) close(); }}
          className="fixed inset-0 z-40 bg-black/40 flex items-center justify-center px-4"
        >
          <div className="bg-white rounded-xl p-5 w-full max-w-md flex flex-col gap-3">
            <h3 className="text-[16px] font-semibold">提交建議</h3>
            <p className="text-[13px] text-gray-500">有任何功能建議或問題回報，都歡迎告訴我們。</p>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="請輸入您的建議…"
              rows={5}
              className="w-full border border-gray-300 rounded-lg p-2 text-[16px] focus:outline-none focus:border-gray-500 resize-none"
            />
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={close}
                disabled={submitting}
                className="px-3 py-1.5 rounded-lg border border-gray-300 text-[13px] text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={submit}
                disabled={submitting || !text.trim()}
                className="px-3 py-1.5 rounded-lg bg-[#1d1d1f] text-white text-[13px] disabled:opacity-50"
              >
                {submitting ? '送出中…' : '送出'}
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-20 right-5 z-50 px-4 py-2 rounded-lg bg-[#1d1d1f] text-white text-[13px] shadow-lg">
          {toast}
        </div>
      )}
    </>
  );
}
