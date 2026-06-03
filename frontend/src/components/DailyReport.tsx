import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useToast } from './Toast'
import { Sparkles, TrendingUp, Target, Zap, BookOpen, ChevronRight } from 'lucide-react'

interface DailyData {
  date: string
  today_new_jobs: number
  score_distribution: { tier: string; cnt: number }[]
  weekly_applications: { status: string; cnt: number }[]
  top_skill_gaps: { skill: string; demand_count: number }[]
  recommended_actions: string[]
  total_matched: number
}

const STATUS_LABELS: Record<string, string> = {
  applied: '已投递', interview: '面试中', offer: '已获Offer', rejected: '已拒绝',
}

const TIER_COLORS: Record<string, string> = {
  '80-100': 'bg-[#10B981]', '60-79': 'bg-yellow-500', '0-59': 'bg-gray-500',
}

export default function DailyReport() {
  const [data, setData] = useState<DailyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [collapsed, setCollapsed] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = async () => {
    try {
      const d = await api.health() // 复用 fetch
      const res = await fetch('/api/daily-report')
      if (res.ok) setData(await res.json())
    } catch {
      toast('info', '日报数据暂不可用')
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-[#1E293B]/80 to-[#0B1120]/80 border border-[#10B981]/10 rounded-2xl p-5 animate-pulse mb-6">
        <div className="h-5 w-32 bg-white/10 rounded mb-4" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          {[1,2,3,4].map(i => <div key={i} className="h-16 bg-white/5 rounded-xl" />)}
        </div>
      </div>
    )
  }

  if (!data) return null

  const appliedTotal = data.weekly_applications.reduce((s, a) => s + a.cnt, 0)
  const offerCount = data.weekly_applications.find(a => a.status === 'offer')?.cnt || 0

  if (collapsed) {
    return (
      <div
        onClick={() => setCollapsed(false)}
        className="bg-gradient-to-r from-[#10B981]/5 to-transparent border border-[#10B981]/10 rounded-xl px-4 py-3 mb-6 cursor-pointer hover:border-[#10B981]/20 transition-all flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <Sparkles className="w-4 h-4 text-[#10B981]" />
          <span className="text-sm text-[#10B981]">
            今日新增 <b>{data.today_new_jobs}</b> 个岗位 · {data.total_matched} 个匹配
          </span>
        </div>
        <ChevronRight className="w-4 h-4 text-gray-500" />
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-br from-[#1E293B]/80 to-[#0B1120]/80 border border-[#10B981]/10 rounded-2xl p-5 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#10B981]" />
          <h3 className="text-sm font-bold text-white">求职日报</h3>
          <span className="text-xs text-gray-500">{data.date}</span>
        </div>
        <button onClick={() => setCollapsed(true)} className="text-xs text-gray-500 hover:text-white transition-colors">
          收起 ▲
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-[#0B1120]/60 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-[#10B981]">{data.today_new_jobs}</div>
          <div className="text-xs text-gray-500 mt-1 flex items-center justify-center gap-1">
            <Zap className="w-3 h-3" /> 今日新增
          </div>
        </div>
        <div className="bg-[#0B1120]/60 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">{data.total_matched}</div>
          <div className="text-xs text-gray-500 mt-1 flex items-center justify-center gap-1">
            <Target className="w-3 h-3" /> 匹配岗位
          </div>
        </div>
        <div className="bg-[#0B1120]/60 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-yellow-400">{appliedTotal}</div>
          <div className="text-xs text-gray-500 mt-1 flex items-center justify-center gap-1">
            <TrendingUp className="w-3 h-3" /> 本周投递
          </div>
        </div>
        <div className="bg-[#0B1120]/60 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-purple-400">{offerCount}</div>
          <div className="text-xs text-gray-500 mt-1 flex items-center justify-center gap-1">
            <Sparkles className="w-3 h-3" /> Offer
          </div>
        </div>
      </div>

      {/* Score Distribution Bar */}
      {data.score_distribution.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-gray-500 mb-2">匹配分分布</div>
          <div className="flex h-5 rounded-full overflow-hidden">
            {data.score_distribution.map(t => {
              const total = data.score_distribution.reduce((s, d) => s + d.cnt, 0)
              const pct = total > 0 ? (t.cnt / total) * 100 : 0
              return (
                <div
                  key={t.tier}
                  className={`${TIER_COLORS[t.tier] || 'bg-gray-500'} transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                  title={`${t.tier}分: ${t.cnt}个`}
                />
              )
            })}
          </div>
          <div className="flex justify-between mt-1">
            {data.score_distribution.map(t => (
              <span key={t.tier} className="text-[10px] text-gray-600">
                {t.tier}分 {t.cnt}个
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Skill Gaps */}
      {data.top_skill_gaps.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
            <BookOpen className="w-3 h-3" /> 市场最需要的技能（你还未掌握）
          </div>
          <div className="flex flex-wrap gap-2">
            {data.top_skill_gaps.map(g => (
              <span key={g.skill}
                className="px-2 py-1 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-400"
              >
                {g.skill}
                <span className="text-yellow-600 ml-1">×{g.demand_count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {data.recommended_actions.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 mb-2">今日建议</div>
          <div className="space-y-1.5">
            {data.recommended_actions.map((a, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="text-[#10B981] mt-0.5">▸</span>
                <span className="text-gray-300">{a}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
