'use client';

type ActionFilter = 'all' | 'BUY' | 'HOLD' | 'SELL';

interface Props {
  actionFilter: ActionFilter;
  onActionChange: (action: ActionFilter) => void;
}

export default function SignalActionFilter({ actionFilter, onActionChange }: Props) {
  return (
    <div className="flex gap-2 flex-wrap">
      {(['all', 'BUY', 'HOLD', 'SELL'] as ActionFilter[]).map((action) => {
        const isActive = actionFilter === action;
        let activeClass = '';
        if (isActive) {
          if (action === 'all') activeClass = 'bg-gray-900 text-white border-transparent';
          else if (action === 'BUY') activeClass = 'bg-green-800 text-white border-transparent';
          else if (action === 'HOLD') activeClass = 'text-white border-transparent';
          else activeClass = 'bg-red-700 text-white border-transparent';
        }
        const label =
          action === 'all' ? '全部' : action === 'BUY' ? '🟢 BUY' : action === 'HOLD' ? '🟡 HOLD' : '🔴 SELL';

        return (
          <button
            key={action}
            onClick={() => onActionChange(action)}
            className={`px-3.5 py-1 rounded-full border text-[13px] cursor-pointer transition-all ${
              isActive
                ? action === 'HOLD'
                  ? 'border-transparent text-white'
                  : activeClass
                : 'border-gray-300 bg-white text-gray-700 hover:border-gray-500'
            }`}
            style={
              isActive && action === 'HOLD' ? { background: '#f57f17' } : undefined
            }
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
