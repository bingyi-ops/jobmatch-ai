import { Link } from 'react-router-dom'
import { ExternalLink, Clock, MapPin, Building2, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Job } from '../types'
import DeadlineBadge from './DeadlineBadge'

const PLATFORM_LABELS: Record<string, { label: string; color: string }> = {
  official: { label: '官网', color: 'bg-blue-500/20 text-blue-400' },
  boss_zhipin: { label: 'Boss直聘', color: 'bg-green-500/20 text-green-400' },
  xiaohongshu: { label: '小红书', color: 'bg-pink-500/20 text-pink-400' },
  wechat_public: { label: '公众号', color: 'bg-orange-500/20 text-orange-400' },
  liepin: { label: '猎聘', color: 'bg-orange-500/20 text-orange-400' },
  lagou: { label: '拉勾', color: 'bg-green-500/20 text-green-400' },
  zhilian: { label: '智联', color: 'bg-blue-500/20 text-blue-400' },
  '51job': { label: '前程无忧', color: 'bg-yellow-500/20 text-yellow-400' },
  shixiseng: { label: '实习僧', color: 'bg-teal-500/20 text-teal-400' },
  zhihu: { label: '知乎', color: 'bg-blue-500/20 text-blue-400' },
  referral: { label: '内推', color: 'bg-purple-500/20 text-purple-400' },
  school_career: { label: '就业网', color: 'bg-cyan-500/20 text-cyan-400' },
  bilibili: { label: 'B站', color: 'bg-pink-500/20 text-pink-400' },
  douyin: { label: '抖音', color: 'bg-white/20 text-white' },
  weibo: { label: '微博', color: 'bg-red-500/20 text-red-400' },
  custom: { label: '自定义', color: 'bg-purple-500/20 text-purple-400' },
}

interface Props {
  job: Job
  matchOverlay?: { overlap_score: number; match_reasons: string }
}

const PLATFORM_META: Record<string, { label: string; dot: string; bg: string; border: string }> = {
  official:       { label: '官网',   dot: 'bg-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/20' },
  boss_zhipin:    { label: 'Boss',    dot: 'bg-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20' },
  xiaohongshu:   { label: '小红书', dot: 'bg-pink-400',  bg: 'bg-pink-500/10',  border: 'border-pink-500/20' },
  wechat_public:  { label: '公众号', dot: 'bg-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
  liepin:        { label: '猎聘',   dot: 'bg-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
  lagou:         { label: '拉勾',   dot: 'bg-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20' },
  zhilian:        { label: '智联',   dot: 'bg-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/20' },
  '51job':       { label: '51Job',   dot: 'bg-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  shixiseng:     { label: '实习僧', dot: 'bg-teal-400',   bg: 'bg-teal-500/10',   border: 'border-teal-500/20' },
  zhihu:         { label: '知乎',   dot: 'bg-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/20' },
  referral:       { label: '内推',   dot: 'bg-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  school_career:  { label: '就业网', dot: 'bg-cyan-400',   bg: 'bg-cyan-500/10',   border: 'border-cyan-500/20' },
  custom:        { label: '自定义', dot: 'bg-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
}

const TYPE_LABELS: Record<string, string> = {
  daily_intern: '日常实习', summer_intern: '暑期实习',
  autumn_recruit: '秋招', spring_recruit: '春招', experienced: '社招',
}

export default function JobCard({ job, matchOverlay }: Props) {
  const [expanded, setExpanded] = useState(false)
  const meta = PLATFORM_META[job.source_platform] || { label: job.source_platform, dot: 'bg-gray-400', bg: 'bg-white/5', border: 'border-white/10' }
  const postedDate = job.posted_at ? new Date(job.posted_at).toLocaleDateString('zh-CN') : ''

  return (
    <div className={`group bg-[#1E293B]/60 border ${meta.border} rounded-xl p-4
      hover:border-[#10B981]/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[#10B981]/5
      transition-all duration-200`}>

      {/* Top row: platform tag + date + match score */}
      <div className="flex items-start justify-between mb-2">
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${meta.bg} ${meta.dot.replace('bg-', 'text-')}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
          {meta.label}
        </span>
        <div className="flex items-center gap-2">
          {matchOverlay && (
            <span className="text-xs font-bold text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded-full">
              {matchOverlay.overlap_score}分
            </span>
          )}
          {postedDate && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" /> {postedDate}
            </span>
          )}
        </div>
      </div>

      {/* Title + Company */}
      <div className="mb-2">
        <a href={job.source_url} target="_blank" rel="noopener noreferrer"
          className="text-[#60A5FA] hover:text-[#93C5FD] font-semibold text-base transition-colors flex items-center gap-1 group-hover:underline">
          {job.title}
          <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-opacity" />
        </a>
        <div className="flex items-center gap-1 text-gray-400 text-sm mt-0.5">
          <Building2 className="w-3.5 h-3.5" />
          {job.company}
        </div>
      </div>

      {/* Meta tags */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        {job.city && (
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <MapPin className="w-3 h-3" /> {job.city}
          </span>
        )}
        {job.salary_range && (
          <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-gray-300">{job.salary_range}</span>
        )}
        {job.recruitment_type && (
          <span className="text-xs px-2 py-0.5 rounded bg-[#10B981]/10 text-[#10B981]">
            {TYPE_LABELS[job.recruitment_type] || job.recruitment_type}
          </span>
        )}
        {job.industry && (
          <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400">{job.industry}</span>
        )}
        {job.application_deadline && <DeadlineBadge deadline={job.application_deadline} />}
      </div>

      {/* JD Summary */}
      {job.jd_text && (
        <div className="mb-3">
          <p className={`text-sm text-gray-400 leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}>
            {job.jd_text}
          </p>
          {job.jd_text.length > 150 && (
            <button onClick={() => setExpanded(!expanded)}
              className="text-xs text-[#10B981] hover:text-[#34D399] mt-1 flex items-center gap-1">
                {expanded ? '收起' : '展开'}
                <ChevronDown className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`} />
              </button>
          )}
        </div>
      )}

      {/* Skills */}
      {Array.isArray(job.jd_skills) && (job.jd_skills as string[]).length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {(job.jd_skills as string[]).slice(0, 6).map(s => (
            <span key={s} className="px-2 py-0.5 bg-[#0B1120] rounded text-xs text-gray-500 hover:text-gray-300 transition-colors cursor-default">
              {s}
            </span>
          ))}
        </div>
      )}

      {/* Action */}
      <Link
        to={`/jobs/${job.id}`}
        className="inline-flex items-center gap-1 text-sm text-[#10B981] hover:text-[#34D399] font-medium transition-colors"
      >
        查看详情 →
      </Link>
    </div>
  )
}
