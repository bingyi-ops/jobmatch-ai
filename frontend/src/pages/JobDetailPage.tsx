import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Job, ResumeProfile, CompanyInfo } from '../types'
import GapAnalysis from '../components/GapAnalysis'
import InterviewPrep from '../components/InterviewPrep'
import CompanySnapshot from '../components/CompanySnapshot'
import SimilarJobs from '../components/SimilarJobs'
import ResumeAdvisor from '../components/ResumeAdvisor'
import DeadlineBadge from '../components/DeadlineBadge'
import { ExternalLink, Loader2, MapPin, Building2, Send, ArrowLeft, Briefcase, Sparkles } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts'

const PLATFORM_LABELS_JD: Record<string, string> = {
  official: '官网', boss_zhipin: 'Boss直聘', xiaohongshu: '小红书', wechat_public: '公众号',
  liepin: '猎聘', lagou: '拉勾', zhilian: '智联招聘', '51job': '前程无忧',
  shixiseng: '实习僧', zhihu: '知乎', referral: '内推', school_career: '就业网',
  bilibili: 'B站', douyin: '抖音', weibo: '微博', custom: '自定义',
}

const TYPE_LABELS: Record<string, string> = {
  daily_intern: '日常实习', summer_intern: '暑期实习',
  autumn_recruit: '秋招', spring_recruit: '春招', experienced: '社招',
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [similar, setSimilar] = useState<any[]>([])
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null)
  const [companyInfoLoading, setCompanyInfoLoading] = useState(false)
  const [userProfile, setUserProfile] = useState<ResumeProfile | null>(null)
  const [applied, setApplied] = useState(false)

  useEffect(() => {
    if (id) {
      loadJob(Number(id))
      loadResumeProfile()
    }
  }, [id])

  const loadJob = async (jobId: number) => {
    setLoading(true)
    try {
      const [jobData, similarData] = await Promise.all([
        api.getJobDetail(jobId),
        api.getSimilarJobs(jobId, 5),
      ])
      setJob(jobData)
      setSimilar(similarData.items || [])

      // Load company info async
      setCompanyInfoLoading(true)
      try {
        const ci = await api.getCompanyInfo(jobId)
        setCompanyInfo(ci)
      } catch {}
      setCompanyInfoLoading(false)
    } catch (e) {
      console.error('Failed to load job:', e)
    }
    setLoading(false)
  }

  const loadResumeProfile = async () => {
    try {
      const p = await api.getResumeProfile()
      setUserProfile(p)
    } catch {}
  }

  const handleApply = async () => {
    if (!job) return
    try {
      await api.createApplication({
        job_id: job.id,
        match_record_id: job.match_record?.id,
      })
      setApplied(true)
    } catch (e) {
      console.error('Apply failed:', e)
    }
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

  const match = job.match_record
  const jdProfile = job.jd_profile
  const radarData = match ? [
    { subject: '我喜欢', value: match.interest_score, fullMark: 100 },
    { subject: '我擅长', value: match.ability_score, fullMark: 100 },
    { subject: '需要', value: match.market_score, fullMark: 100 },
  ] : []

  return (
    <div className="space-y-4">
      {/* Back button */}
      <button onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" /> 返回
      </button>

      {/* ===== TOP: Header + Radar + Scores ===== */}
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-2xl p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Radar */}
          {match && (
            <div className="w-44 h-44 flex-shrink-0 mx-auto lg:mx-0">
              <ResponsiveContainer>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#9CA3AF' }} />
                  <Radar dataKey="value" stroke="#10B981" fill="#10B981" fillOpacity={0.2} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <div>
                <a href={job.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-xl font-bold text-[#60A5FA] hover:text-[#93C5FD] flex items-center gap-2">
                  {job.title}
                  <ExternalLink className="w-4 h-4" />
                </a>
                <p className="text-gray-400 flex items-center gap-1.5 mt-1">
                  <Building2 className="w-4 h-4" /> {job.company}
                </p>
              </div>
              {job.application_deadline && <DeadlineBadge deadline={job.application_deadline} />}
            </div>

            {/* Meta tags */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <MapPin className="w-3 h-3" /> {job.city}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-gray-300">{job.salary_range}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-[#10B981]/10 text-[#10B981]">{TYPE_LABELS[job.recruitment_type]}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400">{job.industry}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-gray-500">
                {PLATFORM_LABELS_JD[job.source_platform] || job.source_platform}
              </span>
              {job.custom_source_name && (
                <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400">
                  {job.custom_source_name}
                </span>
              )}
            </div>

            {/* Scores */}
            {match && (
              <div className="flex items-center gap-6 mb-3">
                {[
                  { label: '喜欢', score: match.interest_score, color: 'text-blue-400' },
                  { label: '擅长', score: match.ability_score, color: 'text-green-400' },
                  { label: '需要', score: match.market_score, color: 'text-orange-400' },
                ].map(s => (
                  <div key={s.label} className="text-center">
                    <div className={`text-lg font-bold ${s.color}`}>{s.score}</div>
                    <div className="text-[10px] text-gray-500">{s.label}</div>
                  </div>
                ))}
                <div className="border-l border-white/10 pl-6">
                  <div className="text-2xl font-bold text-[#10B981]">{match.overlap_score}</div>
                  <div className="text-[10px] text-gray-500">交集综合分</div>
                </div>
              </div>
            )}

            {/* Match reasons */}
            {match?.match_reasons && (
              <p className="text-sm text-gray-500 bg-[#0B1120]/60 rounded-lg p-3 leading-relaxed whitespace-pre-line">
                {match.match_reasons}
              </p>
            )}

            {/* Apply status */}
            {applied && (
              <div className="mt-3 px-4 py-2 bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg text-sm text-[#10B981] flex items-center gap-2">
                ✅ 已生成投递记录，可在「我的投递」中查看
              </div>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-3 mt-4 pt-4 border-t border-white/5">
          <a href={job.source_url} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-sm text-white transition-colors">
            <ExternalLink className="w-4 h-4" /> 查看原文并投递
          </a>
          {!applied && (
            <button onClick={handleApply}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors">
              <Send className="w-4 h-4" /> 我要投递
            </button>
          )}
        </div>
      </div>

      {/* ===== Gap Analysis ===== */}
      {userProfile?.has_resume && (
        <GapAnalysis
          jdProfile={jdProfile}
          userProfile={userProfile.ability_profile}
          scores={match ? { interest: match.interest_score, ability: match.ability_score, market: match.market_score } : undefined}
        />
      )}

      {/* ===== Resume Optimization Flow ===== */}
      {userProfile?.has_resume && (
        <>
          <ResumeAdvisor
            jobId={job.id}
            jobTitle={job.title}
            jobCompany={job.company}
            onGenerateResume={() => navigate(`/optimizer/${job.id}`)}
          />
          {/* Optimization flow link */}
          <div className="bg-gradient-to-r from-[#10B981]/5 via-blue-500/5 to-purple-500/5 border border-[#10B981]/20 rounded-xl p-4 text-center">
            <Sparkles className="w-5 h-5 text-[#10B981] mx-auto mb-2" />
            <p className="text-sm text-white font-medium mb-1">简历优化闭环</p>
            <p className="text-xs text-gray-400 mb-3">
              差距分析 → 修改建议 → 生成简历 → 模拟面试 → 复盘 → 再优化
            </p>
            <button
              onClick={() => navigate(`/optimizer/${job.id}`)}
              className="px-5 py-2 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors inline-flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> 进入完整闭环流程
            </button>
          </div>
        </>
      )}

      {/* ===== Interview Prep ===== */}
      <InterviewPrep
        jobTitle={job.title}
        jdSkills={Array.isArray(job.jd_skills) ? job.jd_skills : []}
        jobId={job.id}
        onReviewClick={() => navigate(`/optimizer/${job.id}`)}
      />

      {/* ===== Company Snapshot ===== */}
      <CompanySnapshot company={job.company} companyInfo={companyInfo} loading={companyInfoLoading} />

      {/* ===== JD Full Text ===== */}
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
          <Briefcase className="w-4 h-4 text-gray-400" /> JD全文
        </h3>
        <div className="bg-[#0B1120]/60 rounded-lg p-4 max-h-[400px] overflow-y-auto">
          <pre className="text-sm text-gray-400 whitespace-pre-wrap font-sans leading-relaxed">
            {job.jd_text}
          </pre>
        </div>
        {/* Skill tags */}
        {Array.isArray(job.jd_skills) && job.jd_skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {job.jd_skills.map((s: string) => (
              <span key={s} className="px-2.5 py-1 bg-[#10B981]/10 text-[#10B981] rounded-full text-xs font-medium">{s}</span>
            ))}
          </div>
        )}
      </div>

      {/* ===== Similar Jobs ===== */}
      <SimilarJobs jobs={similar} />

      {/* Bottom action */}
      <div className="flex justify-center pt-4 pb-8">
        <div className="text-center">
          <a href={job.source_url} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#10B981] hover:bg-[#059669] rounded-xl text-white font-medium transition-colors">
            <Send className="w-4 h-4" /> 查看原文并投递
          </a>
          <p className="text-xs text-gray-600 mt-2">* 信息以招聘原文为准</p>
        </div>
      </div>
    </div>
  )
}
