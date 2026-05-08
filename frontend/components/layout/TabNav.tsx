'use client';

// MN-004: Two-tab navigation bar (新聞 / 股票訊號).

export type TabId = 'news' | 'signals';

interface Props {
  currentTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const TABS: { id: TabId; label: string }[] = [
  { id: 'news', label: '📰 新聞' },
  { id: 'signals', label: '📈 股票訊號' },
];

export default function TabNav({ currentTab, onTabChange }: Props) {
  return (
    <div className="flex gap-1">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-4 py-1.5 rounded-full border text-[13px] font-medium cursor-pointer transition-all ${
            currentTab === tab.id
              ? 'bg-gray-900 text-white border-transparent'
              : 'border-gray-300 bg-white text-gray-500 hover:border-gray-500'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
