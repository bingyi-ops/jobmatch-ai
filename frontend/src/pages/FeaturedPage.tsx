import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { JobCard } from '../types'
import FeaturedJobCard from '../components/FeaturedJobCard'
import Pagination from '../components/Pagination'
import { FeaturedCardSkeleton } from '../components/Skeleton'
import { useToast } from '../components/Toast'
import { Star, Sparkles, Upload, TrendingUp, AlertCircle, SlidersHorizontal, ChevronDown, ChevronUp } from 'lucide-react'

const INDUSTRIES = ['', '互联网', '制造业', '金融', '教育', '医疗', '咨询', '快消']
const CITIES = ['', '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京']

function loadWeights() {
  try { const raw = localStorage.getItem('jm_weights'); if (raw) { const w = JSON.parse(raw); return { w1: w.w1 ?? 50, w2: w.w2 ?? 50, threshold: w.threshold ?? 60 } } } catch {}
  return { w1: 50, w2: 50, threshold: 60 }
}
function saveWeights(w: { w1: number; w2: number; threshold: number }) { localStorage.setItem('jm_weights', JSON.stringify(w)) }

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
  const { toast } = useToast()

  // 权重配置 (localStorage 持久化) — 阈值也从这里取，统一管理
  const [weights, setWeights] = useState(loadWeights)
  const [showWeights, setShowWeights] = useState(false)
  const setW1 = (v: number) => { const w2 = 100 - v; const w = { ...weights, w1: v, w2 }; setWeights(w); saveWeights(w) }
  const setThreshold = (v: number) => { const w = { ...weights, threshold: v }; setWeights(w); saveWeights(w) }

  useEffect(() => {
    checkResume()
  }, [])

  useEffect(() => {
    if (hasResume) loadFeatured(1)
  }, [type, industry, city, hasResume, weights])

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
      const data = await api.getFeatured({ page: p, page_size: 10, min_score: weights.threshold, type, industry, city, w1: weights.w1, w2: weights.w2 })
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
  const hasFilter = type !== '' || industry !== '' || city !== '' || weights.threshold !== 60
  const clearFilters = () => { setType(''); setIndustry(''); setCity(''); setThreshold(60) }

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

        {/* 权重/阈值配置面板 */}
        <div className="bg-[#1E293B]/40 border border-white/5 rounded-xl mb-4 overflow-hidden">
          <button onClick={() => setShowWeights(!showWeights)}
            className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-gray-400 hover:text-white transition-colors">
            <span className="flex items-center gap-2"><SlidersHorizontal className="w-4 h-4" />调分配置 · 我擅长{weights.w1}% 我喜欢{weights.w2}% · 阈值{weights.threshold}分</span>
            {showWeights ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {showWeights && (
            <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
              <div className="grid grid-cols-2 gap-6 text-xs">
                <div>
                  <div className="flex justify-between text-gray-400 mb-1"><span>我擅长</span><span className="text-green-400 font-bold">{weights.w1}%</span></div>
                  <input type="range" min={10} max={90} value={weights.w1} onChange={e => setW1(Number(e.target.value))}
                    className="w-full accent-green-500 h-1.5" />
                  <span className="text-[10px] text-gray-600">简历 vs JD要求</span>
                </div>
                <div>
                  <div className="flex justify-between text-gray-400 mb-1"><span>我喜欢</span><span className="text-blue-400 font-bold">{weights.w2}%</span></div>
                  <input type="range" min={10} max={90} value={weights.w2} onChange={e => {
                    const v = Number(e.target.value); setW1(100 - v)
                  }} className="w-full accent-blue-500 h-1.5" />
                  <span className="text-[10px] text-gray-600">偏好 vs 岗位条件</span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-gray-400">精选阈值</span>
                <input type="range" min={0} max={100} value={weights.threshold} onChange={e => setThreshold(Number(e.target.value))}
                  className="flex-1 accent-[#10B981] h-1.5" />
                <span className="text-[#10B981] font-bold w-8 text-right">{weights.threshold}</span>
                <button onClick={() => { setThreshold(60); setW1(45) }}
                  className="text-gray-500 hover:text-white px-2 py-0.5 rounded bg-white/5">重置</button>
              </div>
            </div>
          )}
        </div>

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
            <input type="range" min="0" max="100" value={weights.threshold} onChange={e => setThreshold(Number(e.target.value))}
              className="w-24 accent-[#10B981]" />
            <span className="text-xs text-[#10B981] font-bold w-8">{weights.threshold}</span>
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
          <TrendingUp className="w-3 h-3" /> 按交集综合分从高到低排列 · 仅展示 ≥ {weights.threshold} 分岗位
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
