import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { JobCard } from '../types'
import FeaturedJobCard from '../components/FeaturedJobCard'
import Pagination from '../components/Pagination'
import { FeaturedCardSkeleton } from '../components/Skeleton'
import { useToast } from '../components/Toast'
import { Star, Sparkles, Upload, TrendingUp, AlertCircle } from 'lucide-react'

const INDUSTRIES = ['', '互联网', '制造业', '金融', '教育', '医疗', '咨询', '快消']
const CITIES = ['', '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京']

export default function FeaturedPage() {
  const [jobs, setJobs] = useState<JobCard[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [todayNew, setTodayNew] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [hasResume, setHasResume] = useState(false)
  const [checkingResume, setCheckingResume] = useState(true)
  const [type, setType] = useState('')
  const [industry, setIndustry] = useState('')
  const [city, setCity] = useState('')
  const [minScore, setMinScore] = useState(60)
  const { toast } = useToast()

  useEffect(() => {
    checkResume()
  }, [])

  useEffect(() => {
    if (hasResume) loadFeatured(1)
  }, [type, industry, city, minScore, hasResume])

  const checkResume = async () => {
    try {
      const profile = await api.getResumeProfile()
      setHasResume(profile.has_resume)
    } catch {
      setHasResume(false)
      toast('warning', '无法检测简历状态，请前往上传')
    }
    setCheckingResume(false)
  }

  const loadFeatured = async (p: number) => {
    setLoading(true)
    setError('')
    try {
      const data = await api.getFeatured({ page: p, page_size: 10, min_score: minScore, type, industry, city })
      setJobs(data.items)
      setTotal(data.total)
      setTodayNew(data.today_new)
      setPage(p)
    } catch (e) {
      setError('加载推荐失败，请稍后重试')
      toast('error', '精选推荐加载失败')
    }
    setLoading(false)
  }

  if (checkingResume) {
    return (
      <div className="space-y-4">
        <FeaturedCardSkeleton />
        <FeaturedCardSkeleton />
        <FeaturedCardSkeleton />
      </div>
    )
  }

  if (!hasResume) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Upload className="w-16 h-16 text-gray-600 mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">上传简历，解锁精选推荐</h2>
        <p className="text-gray-500 mb-6 max-w-md">
          AI 将基于你的简历生成三圈画像（我喜欢 / 我擅长 / 公司需要），为你匹配最合适的岗位
        </p>
        <Link to="/resume" className="px-6 py-3 bg-[#10B981] text-white rounded-xl font-medium hover:bg-[#059669] transition-colors flex items-center gap-2">
          <Sparkles className="w-4 h-4" /> 上传简历
        </Link>
      </div>
    )
  }

  // 是否有筛选条件激活
  const hasFilter = type !== '' || industry !== '' || city !== '' || minScore !== 60
  const clearFilters = () => { setType(''); setIndustry(''); setCity(''); setMinScore(60) }

  return (
    <div>
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Star className="w-5 h-5 text-[#10B981]" />
            精选推荐
            {total > 0 && (
              <span className="text-sm font-normal text-gray-500 ml-2">
                共 {total} 个高匹配岗位
              </span>
            )}
          </h1>
          {/* 上传简历 CTA */}
          <Link to="/resume"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs px-3 py-1.5 bg-[#10B981]/10 text-[#10B981] rounded-lg hover:bg-[#10B981]/20 transition-colors">
            <Upload className="w-3.5 h-3.5" /> 更新简历
          </Link>
        </div>

        {/* Today highlight */}
        {todayNew > 0 && (
          <div className="bg-gradient-to-r from-[#10B981]/20 via-[#059669]/10 to-transparent border border-[#10B981]/20 rounded-xl p-3 mb-4 flex items-center gap-2 animate-pulse">
            <Sparkles className="w-4 h-4 text-[#10B981] animate-bounce" />
            <span className="text-sm text-[#10B981]">
              今日新增 <span className="font-bold text-base">{todayNew}</span> 个高匹配岗位，快去看看！
            </span>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-1 items-center">
          {/* Type */}
          <div className="flex gap-1 flex-wrap">
            {['', 'daily_intern', 'summer_intern', 'autumn_recruit', 'spring_recruit', 'experienced'].map(t => (
              <button key={t} onClick={() => setType(t)}
                className={`px-2.5 py-1 rounded-md text-xs transition-all ${
                  type === t ? 'bg-[#10B981]/20 text-[#10B981] ring-1 ring-[#10B981]/30' : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}>
                {t === '' ? '全部类型' : { daily_intern: '日常实习', summer_intern: '暑期实习', autumn_recruit: '秋招', spring_recruit: '春招', experienced: '社招' }[t] || t}
              </button>
            ))}
          </div>

          {/* Industry */}
          <select value={industry} onChange={e => setIndustry(e.target.value)}
            className="bg-[#1E293B] border border-white/10 rounded-md text-xs text-gray-300 px-2 py-1 focus:border-[#10B981]/50 focus:outline-none">
            <option value="">全部行业</option>
            {INDUSTRIES.filter(Boolean).map(ind => <option key={ind} value={ind}>{ind}</option>)}
          </select>

          {/* City */}
          <select value={city} onChange={e => setCity(e.target.value)}
            className="bg-[#1E293B] border border-white/10 rounded-md text-xs text-gray-300 px-2 py-1 focus:border-[#10B981]/50 focus:outline-none">
            <option value="">全部城市</option>
            {CITIES.filter(Boolean).map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          {/* Min Score */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 whitespace-nowrap">最低分:</span>
            <input type="range" min="0" max="100" value={minScore} onChange={e => setMinScore(Number(e.target.value))}
              className="w-24 accent-[#10B981]" />
            <span className="text-xs text-[#10B981] font-bold w-8">{minScore}</span>
          </div>

          {/* Clear filters */}
          {hasFilter && (
            <button onClick={clearFilters}
              className="text-xs text-gray-500 hover:text-white transition-colors px-2 py-1">
              重置筛选 ✕
            </button>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
          <TrendingUp className="w-3 h-3" /> 按交集综合分从高到低排列 · 仅展示 ≥ {minScore} 分岗位
        </div>
      </div>

      {/* Loading */}
      {loading ? (
        <div className="space-y-4">
          <FeaturedCardSkeleton />
          <FeaturedCardSkeleton />
          <FeaturedCardSkeleton />
        </div>
      ) : error ? (
        <div className="text-center py-20">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 text-red-400/30" />
          <p className="text-red-400/70 mb-3">{error}</p>
          <button onClick={() => loadFeatured(page)} className="text-sm px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-300 transition-colors">重试</button>
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
            <Star className="w-8 h-8 text-gray-600" />
          </div>
          <p className="text-gray-400 mb-1">暂无满足条件的高匹配岗位</p>
          <p className="text-xs text-gray-500 mb-4">试试降低最低分或调整筛选条件</p>
          {hasFilter && (
            <button onClick={clearFilters}
              className="text-xs px-4 py-2 bg-[#10B981]/10 text-[#10B981] rounded-lg hover:bg-[#10B981]/20 transition-colors">
              清除筛选条件
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map(job => <FeaturedJobCard key={`${job.job_id}-${job.id}`} job={job} onFeedback={() => loadFeatured(page)} />)}
        </div>
      )}

      <div className="mt-6">
        <Pagination page={page} total={total} pageSize={10} onChange={loadFeatured} />
      </div>
    </div>
  )
}
