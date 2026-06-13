interface Props {
  platform: string
  type: string
  onPlatformChange: (v: string) => void
  onTypeChange: (v: string) => void
  showType?: boolean
  onAddCustom?: () => void
}

const PLATFORMS = [
  { value: '', label: '全部来源' },
  { value: 'official', label: '企业官网' },
  { value: 'boss_zhipin', label: 'Boss直聘' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'wechat_public', label: '公众号' },
  { value: 'referral', label: '内推' },
  { value: 'school_career', label: '就业网' },
  { value: 'custom', label: '招聘平台' },
]

const TYPES = [
  { value: '', label: '全部类型' },
  { value: 'daily_intern', label: '日常实习' },
  { value: 'summer_intern', label: '暑期实习' },
  { value: 'autumn_recruit', label: '秋招' },
  { value: 'spring_recruit', label: '春招' },
  { value: 'experienced', label: '社招' },
]

function FilterRow({ items, selected, onChange, onAdd }: { items: typeof PLATFORMS; selected: string; onChange: (v: string) => void; onAdd?: () => void }) {
  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      {items.map(item => (
        <button
          key={item.value}
          onClick={() => onChange(item.value)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            selected === item.value
              ? 'bg-[#10B981]/20 text-[#10B981] ring-1 ring-[#10B981]/30'
              : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
          }`}
        >
          {item.label}
        </button>
      ))}
      {onAdd && (
        <button
          onClick={onAdd}
          className="px-3 py-1.5 rounded-md text-xs font-medium bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors border border-purple-500/20"
        >
          + 添加来源
        </button>
      )}
    </div>
  )
}

export default function TwoLevelFilter({ platform, type, onPlatformChange, onTypeChange, showType = true, onAddCustom }: Props) {
  return (
    <div className="space-y-3">
      <FilterRow items={PLATFORMS} selected={platform} onChange={onPlatformChange} onAdd={onAddCustom} />
      {showType && <FilterRow items={TYPES} selected={type} onChange={onTypeChange} />}
    </div>
  )
}
