import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend } from 'recharts'
import { Check, X, AlertTriangle } from 'lucide-react'
import { JdProfile, ResumeProfile } from '../types'

interface Props {
  jdProfile: JdProfile | null
  userProfile: ResumeProfile['ability_profile'] | undefined
  scores?: { interest: number; ability: number; market: number }
}

export default function GapAnalysis({ jdProfile, userProfile, scores }: Props) {
  const jdSkills = jdProfile?.skills || []
  const userSkills = userProfile?.skills?.map(s => s.toLowerCase()) || []

  // Skill comparison
  const skillComparison = jdSkills.map(skill => {
    const lower = skill.toLowerCase()
    const matched = userSkills.some(us => us.includes(lower) || lower.includes(us))
    const partial = !matched && userSkills.some(us => {
      const sWords = lower.split(/\s+/)
      const uWords = us.split(/\s+/)
      return sWords.some(sw => uWords.some(uw => sw.includes(uw) || uw.includes(sw)))
    })
    return { skill, status: matched ? 'matched' as const : partial ? 'partial' as const : 'missing' as const }
  })

  const matchedCount = skillComparison.filter(s => s.status === 'matched').length
  const totalCount = skillComparison.length
  const gapPercent = totalCount > 0 ? Math.round((1 - matchedCount / totalCount) * 100) : 0

  // Radar data for 4 dimensions
  const radarData = [
    { dim: '知识', jd: 75, user: (scores?.interest || 60) },
    { dim: '技能', jd: 85, user: (scores?.ability || 55) },
    { dim: '能力', jd: 80, user: (scores?.market || 65) },
    { dim: '价值观', jd: 70, user: Math.round((scores?.interest || 60) * 0.9) },
  ]

  return (
    <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
        🎯 差距分析
        <span className="text-xs font-normal text-gray-500">
          已匹配 {matchedCount}/{totalCount} 项技能
        </span>
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Skill comparison table */}
        <div className="bg-[#0B1120]/60 rounded-lg p-3">
          <h4 className="text-xs font-medium text-gray-400 mb-2">技能逐项对比</h4>
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {skillComparison.map(({ skill, status }) => (
              <div key={skill} className="flex items-center justify-between py-1.5 px-2 rounded even:bg-white/[0.02]">
                <span className="text-xs text-gray-300">{skill}</span>
                <span className={`flex items-center gap-1 text-xs font-medium ${
                  status === 'matched' ? 'text-[#10B981]' : status === 'partial' ? 'text-orange-400' : 'text-red-400'
                }`}>
                  {status === 'matched' ? <Check className="w-3 h-3" /> : status === 'partial' ? <AlertTriangle className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  {status === 'matched' ? '已匹配' : status === 'partial' ? '部分' : '缺失'}
                </span>
              </div>
            ))}
            {skillComparison.length === 0 && (
              <p className="text-xs text-gray-600 py-2">无技能数据</p>
            )}
          </div>
        </div>

        {/* Radar chart */}
        <div className="bg-[#0B1120]/60 rounded-lg p-3">
          <h4 className="text-xs font-medium text-gray-400 mb-2">四维能力蛛网图</h4>
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="dim" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8, fill: '#6B7280' }} />
              <Radar name="JD要求" dataKey="jd" stroke="#60A5FA" fill="#60A5FA" fillOpacity={0.1} strokeWidth={1.5} />
              <Radar name="当前水平" dataKey="user" stroke="#10B981" fill="#10B981" fillOpacity={0.15} strokeWidth={1.5} />
              <Legend wrapperStyle={{ fontSize: '10px', color: '#9CA3AF' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gap summary */}
      <div className="bg-[#0B1120]/60 rounded-lg p-3 flex items-center justify-between">
        <span className="text-xs text-gray-400">综合差距度</span>
        <div className="flex items-center gap-3">
          <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-[#10B981] via-orange-500 to-red-500 rounded-full"
              style={{ width: `${gapPercent}%` }} />
          </div>
          <span className={`text-sm font-bold ${gapPercent < 30 ? 'text-[#10B981]' : gapPercent < 60 ? 'text-orange-400' : 'text-red-400'}`}>
            {gapPercent}%
          </span>
        </div>
      </div>
    </div>
  )
}
