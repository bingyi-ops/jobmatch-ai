import { useState } from 'react'
import { api } from '../api/client'
import { ResumeAdviseResult } from '../types'
import { Sparkles, Check, AlertTriangle, Lightbulb, FileText, Target, Loader2, ArrowRight } from 'lucide-react'

interface Props {
  jobId: number
  jobTitle: string
  jobCompany: string
  matchedSkills?: string[]
  missingSkills?: string[]
  onGenerateResume?: () => void
}

export default function ResumeAdvisor({ jobId, jobTitle, jobCompany, matchedSkills: initMatched, missingSkills: initMissing, onGenerateResume }: Props) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ResumeAdviseResult | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState<any>(null)

  const getAdvice = async () => {
    setLoading(true)
    try {
      const r = await api.getResumeAdvise(jobId)
      setResult(r)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const generateResume = async () => {
    setGenerating(true)
    try {
      const r = await api.generateResume(jobId)
      setGenerated(r.resume)
      onGenerateResume?.()
    } catch (e) { console.error(e) }
    setGenerating(false)
  }

  const typeIcons: Record<string, any> = {
    strength: { Icon: Check, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
    gap: { Icon: AlertTriangle, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
    project: { Icon: FileText, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    keyword: { Icon: Target, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
    format: { Icon: Lightbulb, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  }

  return (
    <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
        <Sparkles className="w-4 h-4 text-[#10B981]" />
        📝 AI简历修改建议
        <span className="text-xs font-normal text-gray-500">针对 {jobCompany}{jobTitle}</span>
      </h3>

      {!result && !loading && (
        <div className="text-center py-4">
          <p className="text-sm text-gray-400 mb-3">
            基于差距分析结果，AI将给出针对性的简历修改建议，并自动生成优化版简历
          </p>
          <button
            onClick={getAdvice}
            className="px-5 py-2 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors inline-flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> 获取修改建议
          </button>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 text-[#10B981] animate-spin" />
          <span className="ml-2 text-sm text-gray-400">分析差距并生成建议...</span>
        </div>
      )}

      {result && (
        <div className="space-y-3">
          {/* Summary bar */}
          <div className="bg-[#0B1120]/60 rounded-lg p-3 flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500">技能匹配率</span>
              <span className={`text-lg font-bold ml-2 ${result.match_rate >= 60 ? 'text-[#10B981]' : 'text-orange-400'}`}>
                {result.match_rate}%
              </span>
              <span className="text-xs text-gray-600 ml-1">（{result.matched_skills.length}/{result.matched_skills.length + result.missing_skills.length}）</span>
            </div>
            {!generated && (
              <button
                onClick={generateResume}
                disabled={generating}
                className="flex items-center gap-1.5 px-4 py-1.5 bg-[#10B981] hover:bg-[#059669] rounded-lg text-xs text-white font-medium transition-colors disabled:opacity-50"
              >
                {generating ? <Loader2 className="w-3 h-3 animate-spin" /> : <FileText className="w-3 h-3" />}
                {generating ? '生成中...' : '生成优化简历'}
              </button>
            )}
          </div>

          {/* Missing skills */}
          {result.missing_skills.length > 0 && (
            <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3">
              <span className="text-xs font-medium text-red-400">⚠ 技能差距</span>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {result.missing_skills.map(s => (
                  <span key={s} className="px-2 py-0.5 bg-red-500/10 text-red-300 rounded text-xs">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Advices */}
          {result.advices.map((advice, i) => {
            const { Icon, color, bg, border } = typeIcons[advice.type] || typeIcons.format
            return (
              <div key={i} className={`${bg} border ${border} rounded-lg p-3`}>
                <h4 className={`text-xs font-semibold ${color} flex items-center gap-1.5 mb-1.5`}>
                  <Icon className="w-3.5 h-3.5" /> {advice.title}
                </h4>
                <p className="text-xs text-gray-400 leading-relaxed">{advice.content}</p>
                {advice.skills && advice.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {advice.skills.map(s => (
                      <span key={s} className="px-1.5 py-0.5 bg-white/5 rounded text-[10px] text-gray-500">{s}</span>
                    ))}
                  </div>
                )}
              </div>
            )
          })}

          {/* Generated Resume */}
          {generated && (
            <div className="border border-[#10B981]/30 bg-[#10B981]/5 rounded-xl p-4 animate-celebrate">
              <h4 className="text-sm font-semibold text-[#10B981] flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4" /> ✅ 优化简历已生成！
              </h4>
              <p className="text-xs text-gray-500 mb-3">
                共优化 {generated?.optimization_notes?.length || 0} 处，覆盖 {generated?.jd_matched_points?.length || 0} 个JD匹配点
              </p>
              <div className="bg-[#0B1120]/80 rounded-lg p-3 space-y-2 max-h-[300px] overflow-y-auto">
                {/* Summary */}
                <div className="mb-2 pb-2 border-b border-white/5">
                  <span className="text-[10px] text-gray-600 uppercase">求职意向</span>
                  <p className="text-xs text-white mt-0.5">{generated?.target_job} @ {generated?.target_company}</p>
                </div>
                {/* Core skills */}
                <div>
                  <span className="text-[10px] text-gray-600 uppercase">核心技能</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {generated?.core_skills?.map((s: string) => (
                      <span key={s} className="px-2 py-0.5 bg-[#10B981]/10 text-[#10B981] rounded-full text-[10px]">{s}</span>
                    ))}
                  </div>
                </div>
                {/* Projects */}
                <div>
                  <span className="text-[10px] text-gray-600 uppercase">优化后的项目经历</span>
                  {generated?.related_projects?.map((p: any, idx: number) => (
                    <div key={idx} className="mt-1 bg-white/[0.02] rounded p-2">
                      <span className="text-xs text-gray-300 font-medium">{p.name}</span>
                      <p className="text-[11px] text-gray-500 leading-relaxed mt-0.5">{p.description}</p>
                    </div>
                  ))}
                </div>
                {/* JD Matched Points */}
                <div>
                  <span className="text-[10px] text-gray-600 uppercase">JD匹配亮点</span>
                  {generated?.jd_matched_points?.map((p: string, idx: number) => (
                    <p key={idx} className="text-[11px] text-green-400/70 mt-0.5 flex items-start gap-1">
                      <Check className="w-3 h-3 mt-0.5 flex-shrink-0" /> {p}
                    </p>
                  ))}
                </div>
              </div>
              {onGenerateResume && (
                <button
                  onClick={onGenerateResume}
                  className="mt-3 w-full py-2 bg-[#10B981] hover:bg-[#059669] rounded-lg text-sm text-white font-medium transition-colors flex items-center justify-center gap-2"
                >
                  查看简历闭环流程 <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
