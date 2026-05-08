'use client';

// MN-004: Confidence sort toggle button (desc → asc → none cycle).

export type SortOrder = 'desc' | 'asc' | 'none';

interface Props {
  sort: SortOrder;
  onToggle: () => void;
}

export default function SignalSort({ sort, onToggle }: Props) {
  const label =
    sort === 'desc' ? '信心度 ↓' : sort === 'asc' ? '信心度 ↑' : '信心度 ↕';
  const isActive = sort !== 'none';

  return (
    <button
      onClick={onToggle}
      className={`text-[11px] px-2.5 py-0.5 rounded-full border cursor-pointer transition-all ${
        isActive
          ? 'border-gray-500 text-gray-900 font-medium'
          : 'border-gray-300 text-gray-500'
      }`}
    >
      {label}
    </button>
  );
}
