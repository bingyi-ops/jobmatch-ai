import { useNavigate } from 'react-router-dom'
import { ExternalLink, Heart, EyeOff, Send, ShieldCheck, ChevronDown, ChevronUp, Info } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { JobCard } from '../types'
import DeadlineBadge from './DeadlineBadge'
import IgnoreFeedbackModal from './IgnoreFeedbackModal'
import { useState } from 'react'
import { api } from '../api/client'

interface Props {
  job: JobCard
  onFeedback?: () => void
}

const TYPE_LABELS: Record<string, string> = {
  daily_intern: '日常实习', summer_intern: '暑期实习',
  autumn_recruit: '秋招', spring_recruit: '春招', experienced: '社招',
}

export default function FeaturedJobCard({ job, onFeedback }: Props) {
  const navigate = useNavigate()
  const [showIgnoreModal, setShowIgnoreModal] = useState(false)
  const [showDetail, setShowDetail] = useState(false)
  const [feedback, setFeedback] = useState(job.feedback)
  const isNew = job.posted_at && new Date().getTime() - new Date(job.posted_at).getTime() < 24 * 60 * 60 * 1000

  // 评分等级描述
  const scoreLevel = (s: number) => s >= 85 ? '优秀' : s >= 70 ? '良好' : s >= 55 ? '中等' : '待提升'
  const scoreColor = (s: number) => s >= 85 ? 'text-green-400' : s >= 70 ? 'text-blue-400' : s >= 55 ? 'text-yellow-400' : 'text-red-400'
  const scoreBar = (s: number) => s >= 85 ? 'bg-green-500' : s >= 70 ? 'bg-blue-500' : s >= 55 ? 'bg-yellow-500' : 'bg-red-500'

  const radarData = [
    { subject: '我喜欢', value: job.interest_score, fullMark: 100 },
    { subject: '我擅长', value: job.ability_score, fullMark: 100 },
    { subject: '公司需要', value: job.market_score, fullMark: 100 },
  ]

  const handleSave = async () => {
    await api.submitFeedback({ match_record_id: job.id, action: 'saved' })
    setFeedback({ action: 'saved' })
    onFeedback?.()
  }

  const handleIgnore = async (reason?: string) => {
    setShowIgnoreModal(false)
    await api.submitFeedback({ match_record_id: job.id, action: 'ignored', ignore_reason: reason })
    setFeedback({ action: 'ignored', ignore_reason: reason })
    onFeedback?.()
  }

  const handleApply = async () => {
    await api.createApplication({ job_id: job.job_id, match_record_id: job.id })
    navigate('/applications')
  }

  if (feedback?.action === 'ignored') return null

  // 进度条渐变配色
  const barColor = job.overlap_score >= 80
    ? 'bg-gradient-to-r from-emerald-400 to-[#10B981]'
    : job.overlap_score >= 60
    ? 'bg-gradient-to-r from-yellow-400 to-orange-400'
    : 'bg-gradient-to-r from-gray-500 to-gray-400'

  return (
    <>
      <div className="group bg-[#1E293B]/60 border border-[#10B981]/10 rounded-xl p-4
        hover:border-[#10B981]/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[#10B981]/5
        transition-all duration-200">

        <div className="flex gap-4">
          {/* Radar thumbnail */}
          <div className="w-20 h-20 flex-shrink-0 hidden sm:block">
            <ResponsiveContainer width={80} height={80}>
              <RadarChart cx={40} cy={40} outerRadius={32} data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 7, fill: '#9CA3AF' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="匹配" dataKey="value" stroke="#10B981" fill="#10B981" fillOpacity={0.2} strokeWidth={1.5} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-1">
              <div className="flex items-center gap-2 flex-wrap">
                {isNew && (
                  <span className="px-1.5 py-0.5 bg-red-500 text-white text-[10px] rounded font-bold animate-pulse">NEW</span>
                )}
                <a href={job.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-[#60A5FA] hover:text-[#93C5FD] font-semibold text-sm flex items-center gap-1 group-hover:underline">
                  {job.title}
                  <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-100 transition-opacity" />
                </a>
              </div>
              {job.application_deadline && <DeadlineBadge deadline={job.application_deadline} />}
            </div>
            <p className="text-gray-400 text-xs mb-1">{job.company} · {job.city} · {job.salary_range}</p>

            {/* Labels */}
            <div className="flex flex-wrap gap-1 mb-2">
              <span className="text-xs px-1.5 py-0.5 rounded bg-[#10B981]/10 text-[#10B981]">
                {TYPE_LABELS[job.recruitment_type] || job.recruitment_type}
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400">{job.industry}</span>
              {(job as any).quality_score > 0 && (
                <span className={`text-xs px-1.5 py-0.5 rounded inline-flex items-center gap-0.5 ${
                  (job as any).quality_score >= 70 ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'
                }`}>
                  <ShieldCheck className="w-2.5 h-2.5" />
                  {(job as any).quality_score}
                </span>
              )}
            </div>

            {/* Scores */}
            <div className="flex gap-3 mb-2">
              {[
                { label: '喜欢', score: job.interest_score, color: 'text-blue-400' },
                { label: '擅长', score: job.ability_score, color: 'text-green-400' },
                { label: '需要', score: job.market_score, color: 'text-orange-400' },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className={`text-sm font-bold ${s.color}`}>{s.score}</div>
                  <div className="text-[10px] text-gray-500">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Overlap score bar */}
            <div className="mb-2">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs text-gray-500">综合匹配</span>
                <span className={`text-sm font-bold ${
                  job.overlap_score >= 80 ? 'text-[#10B981]' :
                  job.overlap_score >= 60 ? 'text-orange-400' : 'text-gray-400'
                }`}>{job.overlap_score}</span>
              </div>
              <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${barColor}`}
                  style={{ width: `${Math.max(job.overlap_score, 5)}%` }}
                />
              </div>
            </div>

            {/* Reasons */}
            {job.match_reasons && (
              <p className="text-xs text-gray-500 line-clamp-2 mb-2">{job.match_reasons}</p>
            )}

            {/* 评分详情展开按钮 */}
            <button onClick={() => setShowDetail(!showDetail)}
              className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-gray-400 transition-colors mb-2">
              {showDetail ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showDetail ? '收起评分详情' : '查看评分详情'}
            </button>

            {/* 展开的评分详情 */}
            {showDetail && (
              <div className="bg-[#0B1120] rounded-lg p-3 mb-3 space-y-2 border border-white/5">
                <p className="text-[10px] text-gray-500 flex items-center gap-1 mb-1">
                  <Info className="w-3 h-3" /> 三圈评分明细
                  <span className="text-gray-600">（0-100分制）</span>
                </p>
                {[
                  { label: '我擅长', sub: '学历+技能+项目', score: job.ability_score, icon: '🧠' },
                  { label: '公司需要', sub: '学历达标+专业对口+经验+职责+稳定性', score: job.market_score, icon: '🏢' },
                  { label: '我喜欢', sub: '城市+行业+薪资+岗位方向', score: job.interest_score, icon: '❤️' },
                ].map(dim => (
                  <div key={dim.label}>
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[11px] text-gray-400">
                        {dim.icon} {dim.label}
                        <span className="text-gray-600 ml-1">· {dim.sub}</span>
                      </span>
                      <span className={`text-[11px] font-bold ${scoreColor(dim.score)}`}>
                        {dim.score}分 <span className="font-normal text-[10px]">{scoreLevel(dim.score)}</span>
                      </span>
                    </div>
                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${scoreBar(dim.score)}`}
                        style={{ width: `${Math.max(dim.score, 2)}%` }} />
                    </div>
                  </div>
                ))}
                <div className="pt-1.5 border-t border-white/5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-gray-300 font-semibold">综合匹配度</span>
                    <span className={`text-sm font-bold ${job.overlap_score >= 80 ? 'text-[#10B981]' : job.overlap_score >= 60 ? 'text-orange-400' : 'text-gray-400'}`}>
                      {job.overlap_score}分
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-600 mt-1">
                    {job.overlap_score >= 80 ? '强烈推荐投递，三圈匹配度均优秀' :
                     job.overlap_score >= 65 ? '推荐投递，部分维度有提升空间' :
                     job.overlap_score >= 50 ? '可关注，建议针对性优化简历或拓宽偏好' :
                     '匹配度偏低，建议提升技能或调整岗位期望'}
                  </p>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button onClick={() => navigate(`/jobs/${job.job_id}`)}
                className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-gray-300 transition-colors">
                查看详情
              </button>
              <button onClick={handleApply}
                className="text-xs px-3 py-1.5 bg-[#10B981]/20 hover:bg-[#10B981]/30 rounded-lg text-[#10B981] flex items-center gap-1 transition-colors">
                <Send className="w-3 h-3" /> 投递
              </button>
              <button onClick={handleSave}
                className={`text-xs p-1.5 rounded-lg transition-colors ${feedback?.action === 'saved' ? 'text-pink-400 bg-pink-500/10' : 'text-gray-500 hover:text-pink-400 hover:bg-pink-500/5'}`}>
                <Heart className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => setShowIgnoreModal(true)}
                className="text-xs p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors">
                <EyeOff className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
      {showIgnoreModal && (
        <IgnoreFeedbackModal onClose={() => setShowIgnoreModal(false)} onConfirm={handleIgnore} />
      )}
    </>
  )
}
