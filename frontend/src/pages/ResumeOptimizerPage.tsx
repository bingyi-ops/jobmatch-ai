import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import ResumeAdvisor from '../components/ResumeAdvisor'
import InterviewReview from '../components/InterviewReview'
import { ArrowLeft, ChevronRight, Check, Sparkles, Target, FileText, MessageSquare, TrendingUp, RotateCcw, Loader2 } from 'lucide-react'

type FlowStep = 'gap' | 'advise' | 'generate' | 'interview' | 'review' | 'improve' | 'revise'

const STEPS: { id: FlowStep; label: string; icon: any; desc: string }[] = [
  { id: 'gap', label: '差距分析', icon: Target, desc: 'JD vs 简历' },
  { id: 'advise', label: '修改建议', icon: FileText, desc: 'AI建议' },
  { id: 'generate', label: '生成简历', icon: Sparkles, desc: '优化版简历' },
  { id: 'interview', label: '模拟面试', icon: MessageSquare, desc: '实战练习' },
  { id: 'review', label: '面试复盘', icon: TrendingUp, desc: '上传总结' },
  { id: 'improve', label: '提升建议', icon: Target, desc: '再优化' },
  { id: 'revise', label: '再次修改', icon: RotateCcw, desc: '迭代简历' },
]

export default function ResumeOptimizerPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const jobId = id ? Number(id) : 0

  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentStep, setCurrentStep] = useState<FlowStep>('gap')
  const [completedSteps, setCompletedSteps] = useState<Set<FlowStep>>(new Set())
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [reviewData, setReviewData] = useState<any>(null)
  const [applicationId, setApplicationId] = useState<number | undefined>()

  useEffect(() => {
    if (jobId) loadJob()
  }, [jobId])

  const loadJob = async () => {
    setLoading(true)
    try {
      const jobData = await api.getJobDetail(jobId)
      setJob(jobData)
      // Check existing application
      try {
        const apps = await api.getApplications({ page: 1, page_size: 20 })
        const existingApp = apps.items?.find((a: any) => a.job_id === jobId)
        if (existingApp) setApplicationId(existingApp.id)
      } catch {}
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const markComplete = (step: FlowStep) => {
    setCompletedSteps(prev => new Set(prev).add(step))
  }

  const goToStep = (step: FlowStep) => {
    setCurrentStep(step)
  }

  const handleAdviseComplete = () => {
    markComplete('advise')
    setCurrentStep('generate')
  }

  const handleGenerateComplete = () => {
    markComplete('generate')
    setCurrentStep('interview')
  }

  const handleInterviewComplete = () => {
    markComplete('interview')
    setCurrentStep('review')
  }

  const handleReviewSubmit = (data: any) => {
    setReviewData(data)
    markComplete('review')
    setShowReviewModal(false)
    setCurrentStep('improve')
  }

  const handleImproveComplete = () => {
    markComplete('improve')
    setCurrentStep('revise')
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 text-[#10B981] animate-spin" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="text-center py-20 text-gray-500">
        <p>岗位未找到</p>
        <button onClick={() => navigate(-1)} className="text-[#10B981] mt-2">← 返回</button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> 返回岗位详情
        </button>
        <span className="text-xs text-gray-600">{job.job_company || job.company} · {job.job_title || job.title}</span>
      </div>

      <h1 className="text-xl font-bold text-white flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-[#10B981]" />
        简历优化闭环
        <span className="text-sm font-normal text-gray-500">差距 → 建议 → 生成 → 面试 → 复盘 → 再优化</span>
      </h1>

      {/* Flow Stepper */}
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
        <div className="flex items-center overflow-x-auto">
          {STEPS.map((step, idx) => {
            const Icon = step.icon
            const isActive = currentStep === step.id
            const isDone = completedSteps.has(step.id)
            return (
              <div key={step.id} className="flex items-center flex-shrink-0">
                <button
                  onClick={() => goToStep(step.id)}
                  className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-[#10B981]/10 text-[#10B981]'
                      : isDone
                      ? 'bg-green-500/5 text-green-500/60'
                      : 'text-gray-600 hover:text-gray-400'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    isActive ? 'bg-[#10B981]/20' : isDone ? 'bg-green-500/10' : 'bg-white/5'
                  }`}>
                    {isDone ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                  </div>
                  <span className="text-[10px] font-medium">{step.label}</span>
                  <span className="text-[8px] opacity-60">{step.desc}</span>
                </button>
                {idx < STEPS.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-gray-700 mx-1" />
                )}
              </div>
            )
          })}
        </div>

        {/* Progress bar */}
        <div className="mt-3 w-full h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#10B981] to-blue-500 rounded-full transition-all duration-500"
            style={{ width: `${(completedSteps.size / STEPS.length) * 100}%` }}
          />
        </div>
        <div className="text-[10px] text-gray-600 mt-1">
          进度 {completedSteps.size}/{STEPS.length} 步骤
        </div>
      </div>

      {/* Current Step Content */}
      <div className="space-y-4">
        {/* Step: Gap Analysis */}
        {currentStep === 'gap' && (
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-400" /> 第一步：差距分析
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#0B1120]/60 rounded-lg p-4">
                <h4 className="text-xs font-medium text-blue-400 mb-2">📍 岗位要求</h4>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(job.jd_skills) ? job.jd_skills : []).map((s: string) => (
                    <span key={s} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded text-xs">{s}</span>
                  ))}
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  <p>公司：{job.job_company || job.company}</p>
                  <p>地点：{job.city}</p>
                  <p>薪资：{job.salary_range}</p>
                </div>
              </div>
              <div className="bg-[#0B1120]/60 rounded-lg p-4">
                <h4 className="text-xs font-medium text-green-400 mb-2">👤 你的简历</h4>
                <p className="text-xs text-gray-400 mb-2">基于已上传简历的画像分析</p>
                <button
                  onClick={() => goToStep('advise')}
                  className="w-full py-2 bg-[#10B981] hover:bg-[#059669] rounded-lg text-xs text-white font-medium transition-colors"
                >
                  查看AI修改建议 →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Resume Advise */}
        {currentStep === 'advise' && (
          <ResumeAdvisor
            jobId={jobId}
            jobTitle={job.title || job.job_title}
            jobCompany={job.company || job.job_company}
            onGenerateResume={handleAdviseComplete}
          />
        )}

        {/* Step: Generate Resume */}
        {currentStep === 'generate' && (
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6 text-center">
            <Sparkles className="w-12 h-12 text-[#10B981] mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-white mb-2">优化简历已生成</h3>
            <p className="text-xs text-gray-400 max-w-sm mx-auto mb-4">
              简历已针对 {job.company || job.job_company} 的 {job.title || job.job_title} 岗位进行了优化，
              请回到上一步查看详细内容。接下来可以进行模拟面试练习。
            </p>
            <div className="flex justify-center gap-3">
              <button onClick={() => goToStep('advise')}
                className="px-4 py-2 bg-white/5 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">
                ← 查看详情
              </button>
              <button onClick={handleInterviewComplete}
                className="px-5 py-2 bg-[#10B981] hover:bg-[#059669] rounded-lg text-sm text-white font-medium transition-colors">
                进入模拟面试 →
              </button>
            </div>
          </div>
        )}

        {/* Step: Interview */}
        {currentStep === 'interview' && (
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-purple-400" /> 第三步：模拟面试
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              回到岗位详情页面进行模拟面试，面试完成后回来提交复盘总结
            </p>
            <div className="flex gap-3">
              <a
                href={`/jobs/${jobId}`}
                className="px-4 py-2 bg-purple-500/10 text-purple-400 rounded-lg text-sm hover:bg-purple-500/20 transition-colors inline-block"
              >
                返回岗位详情进行面试 →
              </a>
              <button onClick={handleInterviewComplete}
                className="px-4 py-2 bg-[#10B981] hover:bg-[#059669] rounded-lg text-sm text-white font-medium transition-colors">
                已完成面试，开始复盘 →
              </button>
            </div>
          </div>
        )}

        {/* Step: Review */}
        {currentStep === 'review' && (
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-orange-400" /> 第四步：面试复盘
            </h3>
            {reviewData ? (
              <div className="space-y-3">
                <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-3">
                  <span className="text-xs text-[#10B981]">✅ 复盘已完成！AI得分：{Math.round(reviewData.analysis?.overall_score || 0)}分</span>
                </div>
                <button onClick={() => setShowReviewModal(true)}
                  className="text-xs text-gray-400 underline hover:text-white">
                  重新提交复盘
                </button>
                <button onClick={() => { markComplete('review'); setCurrentStep('improve') }}
                  className="ml-3 text-xs text-[#10B981] underline">
                  查看提升建议 →
                </button>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-gray-400 mb-3">回顾面试过程，提交你的复盘总结</p>
                <button onClick={() => setShowReviewModal(true)}
                  className="px-5 py-2 bg-[#10B981] hover:bg-[#059669] rounded-lg text-sm text-white font-medium transition-colors">
                  填写复盘总结
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step: Improve */}
        {currentStep === 'improve' && (
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-yellow-400" /> 第五步：提升建议
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              基于面试复盘，AI将给出针对性的提升建议，帮助你在下次面试中表现更好。
            </p>
            <div className="space-y-3">
              <button onClick={() => setShowReviewModal(true)}
                className="w-full py-3 bg-orange-500/10 border border-orange-500/20 rounded-xl text-sm text-orange-400 font-medium hover:bg-orange-500/20 transition-colors">
                查看详细提升建议和简历优化方案
              </button>
              <button onClick={handleImproveComplete}
                className="w-full py-3 bg-[#10B981] hover:bg-[#059669] rounded-lg text-sm text-white font-medium transition-colors">
                查看完整分析 → 准备再次优化简历
              </button>
            </div>
          </div>
        )}

        {/* Step: Revise */}
        {currentStep === 'revise' && (
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6 text-center">
            <RotateCcw className="w-12 h-12 text-[#10B981] mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-white mb-2">闭环完成！开启新一轮优化</h3>
            <p className="text-xs text-gray-400 max-w-sm mx-auto mb-4">
              你已经完成了完整的「差距分析 → 简历优化 → 模拟面试 → 复盘 → 提升建议」闭环。
              现在可以基于最新反馈重新优化简历。
            </p>
            <div className="flex justify-center gap-3">
              <button onClick={() => {
                setCompletedSteps(new Set())
                setCurrentStep('gap')
              }}
                className="px-4 py-2 bg-white/5 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">
                重新开始闭环
              </button>
              <button onClick={() => goToStep('advise')}
                className="px-5 py-2 bg-[#10B981] hover:bg-[#059669] rounded-lg text-sm text-white font-medium transition-colors">
                基于反馈再次优化简历 →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Review Modal */}
      {showReviewModal && (
        <InterviewReview
          jobId={jobId}
          jobTitle={job.title || job.job_title}
          jobCompany={job.company || job.job_company}
          applicationId={applicationId}
          onClose={() => setShowReviewModal(false)}
          onSubmitted={handleReviewSubmit}
        />
      )}
    </div>
  )
}
