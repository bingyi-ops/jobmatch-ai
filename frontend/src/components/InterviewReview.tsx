import { useState } from 'react'
import { api } from '../api/client'
import { AIAnalysis, ImprovementAdvice } from '../types'
import { MessageSquare, Star, Loader2, Send, X, ThumbsUp, ThumbsDown, TrendingUp, BarChart3, Check } from 'lucide-react'

interface Props {
  jobId: number
  jobTitle: string
  jobCompany: string
  applicationId?: number
  onClose: () => void
  onSubmitted?: (data: any) => void
}

export default function InterviewReview({ jobId, jobTitle, jobCompany, applicationId, onClose, onSubmitted }: Props) {
  const [step, setStep] = useState<'form' | 'result' | 'improvement'>('form')
  const [reviewText, setReviewText] = useState('')
  const [scoreSelf, setScoreSelf] = useState(0)
  const [difficultQuestions, setDifficultQuestions] = useState('')
  const [questionsAsked, setQuestionsAsked] = useState<string[]>(['', '', ''])
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null)
  const [advices, setAdvices] = useState<ImprovementAdvice[]>([])
  const [improvementData, setImprovementData] = useState<any>(null)

  const submitReview = async () => {
    if (!reviewText.trim()) return
    setLoading(true)
    try {
      const result = await api.submitInterviewReview({
        job_id: jobId,
        application_id: applicationId,
        review_text: reviewText,
        score_self: scoreSelf,
        questions_asked: questionsAsked.filter(q => q.trim()),
        difficult_questions: difficultQuestions,
      })
      setAnalysis(result.analysis)
      setAdvices(result.improvement_advices)
      setStep('result')
      onSubmitted?.(result)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const getImprovementAdvices = async () => {
    setLoading(true)
    try {
      const result = await api.getImprovementAdvices({ job_id: jobId })
      setImprovementData(result)
      setStep('improvement')
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-[#1E293B] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-[#10B981]" />
            {step === 'form' ? '面试复盘总结' : step === 'result' ? 'AI面试分析' : '提升建议'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
        </div>

        <div className="p-4">
          {/* Step 1: Review Form */}
          {step === 'form' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span className="px-2 py-0.5 bg-white/5 rounded">{jobCompany}</span>
                <span>{jobTitle}</span>
              </div>

              {/* Self Score */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">自我评分（1-10分）</label>
                <div className="flex gap-1">
                  {Array.from({ length: 10 }, (_, i) => i + 1).map(n => (
                    <button
                      key={n}
                      onClick={() => setScoreSelf(n)}
                      className={`w-8 h-8 rounded-lg text-xs font-medium transition-colors ${
                        scoreSelf >= n
                          ? 'bg-[#10B981] text-white'
                          : 'bg-white/5 text-gray-500 hover:bg-white/10'
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>

              {/* Questions Asked */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">面试官问了哪些问题？（至少填1个）</label>
                {questionsAsked.map((q, i) => (
                  <input
                    key={i}
                    value={q}
                    onChange={e => {
                      const updated = [...questionsAsked]
                      updated[i] = e.target.value
                      setQuestionsAsked(updated)
                    }}
                    placeholder={`问题 ${i + 1}：例如"请描述一个你解决过的技术难题"`}
                    className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2.5 text-sm text-white placeholder-gray-600 mb-2 focus:outline-none focus:border-[#10B981]/50"
                  />
                ))}
              </div>

              {/* Difficult Questions */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">哪些问题让你觉得困难？</label>
                <textarea
                  value={difficultQuestions}
                  onChange={e => setDifficultQuestions(e.target.value)}
                  placeholder="描述面试中遇到的难题，AI会帮你分析如何应对..."
                  rows={2}
                  className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2.5 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-[#10B981]/50"
                />
              </div>

              {/* Review Text */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">整体复盘总结</label>
                <textarea
                  value={reviewText}
                  onChange={e => setReviewText(e.target.value)}
                  placeholder="回顾整个面试过程：你表现好的地方、不足的地方、面试官的反应、意外的问题..."
                  rows={5}
                  className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-3 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-[#10B981]/50"
                />
              </div>

              <button
                onClick={submitReview}
                disabled={loading || !reviewText.trim() || scoreSelf === 0}
                className="w-full py-3 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {loading ? 'AI分析中...' : '提交复盘并获取AI分析'}
              </button>
            </div>
          )}

          {/* Step 2: AI Analysis Result */}
          {step === 'result' && analysis && (
            <div className="space-y-4">
              {/* Overall Score */}
              <div className="text-center p-4 bg-[#0B1120]/60 rounded-xl">
                <BarChart3 className="w-8 h-8 text-[#10B981] mx-auto mb-2" />
                <div className="text-3xl font-bold text-[#10B981]">{Math.round(analysis.overall_score)}</div>
                <p className="text-xs text-gray-500 mt-1">综合评分</p>
              </div>

              {/* Score Breakdown */}
              <div className="grid grid-cols-4 gap-2">
                {Object.entries(analysis.score_breakdown).map(([key, val]) => (
                  <div key={key} className="bg-[#0B1120]/60 rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-white">{val}</div>
                    <div className="text-[10px] text-gray-500">
                      {{technical: '技术', communication: '沟通', problem_solving: '解题', culture_fit: '文化'}[key]}
                    </div>
                  </div>
                ))}
              </div>

              {/* Strengths */}
              <div className="bg-[#10B981]/5 border border-[#10B981]/20 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-[#10B981] flex items-center gap-1.5 mb-2">
                  <ThumbsUp className="w-3.5 h-3.5" /> 表现亮点
                </h4>
                <ul className="space-y-1">
                  {analysis.strengths.map((s, i) => (
                    <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                      <Check className="w-3 h-3 text-[#10B981] mt-0.5 flex-shrink-0" /> {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Weaknesses */}
              <div className="bg-orange-500/5 border border-orange-500/20 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-orange-400 flex items-center gap-1.5 mb-2">
                  <ThumbsDown className="w-3.5 h-3.5" /> 待提升点
                </h4>
                <ul className="space-y-1">
                  {analysis.weaknesses.map((s, i) => (
                    <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                      <span className="text-orange-400 mt-0.5">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Key Takeaways */}
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-blue-400 mb-1">💡 核心总结</h4>
                <p className="text-xs text-gray-400">{analysis.key_takeaways}</p>
              </div>

              {/* Advices preview */}
              {advices.slice(0, 2).map((advice, i) => (
                <div key={i} className="bg-[#0B1120]/60 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-white">{advice.category}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      advice.priority === 'high' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                    }`}>{advice.priority === 'high' ? '高优' : '中优'}</span>
                  </div>
                  <p className="text-xs text-gray-400">{advice.action}</p>
                  <p className="text-[10px] text-gray-600 mt-1">⏱ {advice.timeline} | 📚 {advice.resources}</p>
                </div>
              ))}

              <button
                onClick={getImprovementAdvices}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-[#10B981]/20 to-[#10B981]/10 border border-[#10B981]/30 rounded-xl text-sm text-[#10B981] font-medium hover:bg-[#10B981]/20 transition-colors flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
                查看详细提升建议和简历优化方案
              </button>
            </div>
          )}

          {/* Step 3: Improvement Plan */}
          {step === 'improvement' && improvementData && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                <BarChart3 className="w-4 h-4 text-[#10B981]" />
                自评 {improvementData.review_score}分 / AI评分 {Math.round(improvementData.ai_score)}分
              </div>

              {/* Immediate next steps */}
              <div>
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#10B981]" /> 下一步行动计划
                </h4>
                <div className="space-y-2">
                  {improvementData.next_steps.before_next_interview.map((step: any) => (
                    <div key={step.step} className="bg-[#0B1120]/60 rounded-lg p-3 flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-[#10B981]/20 text-[#10B981] flex items-center justify-center text-xs font-bold flex-shrink-0">
                        {step.step}
                      </div>
                      <div>
                        <span className="text-xs font-medium text-white">{step.action}</span>
                        <p className="text-xs text-gray-500 mt-0.5">{step.detail}</p>
                        <span className="text-[10px] text-gray-600">⏱ {step.duration}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Improvement Advices */}
              <div>
                <h4 className="text-sm font-semibold text-white mb-3">提升建议</h4>
                <div className="space-y-2">
                  {improvementData.improvement_advices.map((advice: ImprovementAdvice, i: number) => (
                    <div key={i} className="bg-[#0B1120]/60 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-white">{advice.category}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                          advice.priority === 'high' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                        }`}>{advice.priority === 'high' ? '高优先级' : '中优先级'}</span>
                      </div>
                      <p className="text-xs text-gray-400">{advice.action}</p>
                      <div className="flex gap-3 mt-1 text-[10px] text-gray-600">
                        <span>⏱ {advice.timeline}</span>
                        <span>📚 {advice.resources}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Resume update suggestions */}
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-blue-400 mb-2">📝 简历再次优化建议</h4>
                <ul className="space-y-1">
                  {improvementData.next_steps.resume_update_suggestions.map((s: string, i: number) => (
                    <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                      <Check className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" /> {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Long term growth */}
              <div className="bg-purple-500/5 border border-purple-500/20 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-purple-400 mb-2">🌱 长期成长建议</h4>
                <ul className="space-y-1">
                  {improvementData.next_steps.long_term_growth.map((s: string, i: number) => (
                    <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                      <span className="text-purple-400 mt-0.5">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={onClose}
                className="w-full py-2.5 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors"
              >
                完成复盘，返回
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
