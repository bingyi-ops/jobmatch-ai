import { useState } from 'react'
import { ChevronDown, ChevronUp, Building2, DollarSign, Users, Trophy, Newspaper, Heart } from 'lucide-react'

interface Props {
  company: string
  companyInfo?: {
    funding_stage?: string
    employee_scale?: string
    industry_position?: string
    recent_news?: string
    culture_keywords?: string[]
    disclaimer?: string
  } | null
  loading?: boolean
}

export default function CompanySnapshot({ company, companyInfo, loading }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (loading) {
    return (
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-white/10 rounded w-1/3" />
          <div className="h-3 bg-white/5 rounded w-2/3" />
          <div className="h-3 bg-white/5 rounded w-1/2" />
        </div>
      </div>
    )
  }

  const info = companyInfo || {}

  const items = [
    { icon: <DollarSign className="w-3.5 h-3.5" />, label: '融资/规模', value: info.funding_stage || '信息暂缺' },
    { icon: <Users className="w-3.5 h-3.5" />, label: '员工规模', value: info.employee_scale || '信息暂缺' },
    { icon: <Trophy className="w-3.5 h-3.5" />, label: '行业地位', value: info.industry_position || '信息暂缺' },
    { icon: <Newspaper className="w-3.5 h-3.5" />, label: '近期动态', value: info.recent_news || '暂无' },
  ]

  return (
    <div className="bg-[#1E293B]/80 border border-white/5 rounded-xl p-4 backdrop-blur">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Building2 className="w-4 h-4 text-[#60A5FA]" />
          {company}
        </h3>
        <button onClick={() => setExpanded(!expanded)}
          className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1">
          {expanded ? '收起' : '展开'} {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Compact view */}
      <div className="grid grid-cols-2 gap-2">
        {items.map((item, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className="text-gray-500">{item.icon}</span>
            <span className="text-gray-600">{item.label}:</span>
            <span className="text-gray-300 truncate">{item.value}</span>
          </div>
        ))}
      </div>

      {/* Expanded */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/5 space-y-2">
          {/* Culture keywords */}
          {info.culture_keywords && info.culture_keywords.length > 0 && (
            <div>
              <span className="text-xs text-gray-500 flex items-center gap-1 mb-1.5">
                <Heart className="w-3 h-3" /> 企业文化
              </span>
              <div className="flex flex-wrap gap-1">
                {info.culture_keywords.map((k, i) => (
                  <span key={i} className="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded text-xs">{k}</span>
                ))}
              </div>
            </div>
          )}

          {/* Items in detail */}
          {items.map((item, i) => (
            <div key={i} className="text-xs">
              <span className="text-gray-500">{item.label}: </span>
              <span className="text-gray-300">{item.value}</span>
            </div>
          ))}

          {/* Disclaimer */}
          <div className="text-[10px] text-gray-600 italic border-t border-white/5 pt-2 mt-2">
            ⚠ {info.disclaimer || '基于公开信息推断，仅供参考'}
          </div>
        </div>
      )}

      {!expanded && (
        <div className="text-[10px] text-gray-700 mt-2">
          {info.disclaimer || '基于公开信息推断，仅供参考'}
        </div>
      )}
    </div>
  )
}
