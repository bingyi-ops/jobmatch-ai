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

function ScoringStandards() {
  const [open, setOpen] = useState(false)
  const STANDARD = [
    {dim:'skills',label:'技能匹配',target:'ability',icon:'💡'},{dim:'projects',label:'项目经验',target:'ability',icon:'🔨'},{dim:'education',label:'学历层次',target:'ability',icon:'🎓'},
    {dim:'edu_req',label:'学历达标',target:'market',icon:'📋'},{dim:'major_match',label:'专业对口',target:'market',icon:'📚'},{dim:'exp_years',label:'经验年限',target:'market',icon:'⏳'},
    {dim:'duty_coverage',label:'职责覆盖',target:'market',icon:'📝'},{dim:'stability',label:'工作稳定',target:'market',icon:'🔒'},
    {dim:'city',label:'城市匹配',target:'interest',icon:'🏙️'},{dim:'industry',label:'行业匹配',target:'interest',icon:'🏭'},{dim:'salary',label:'薪资匹配',target:'interest',icon:'💰'},{dim:'role',label:'岗位方向',target:'interest',icon:'🎯'},
  ]
  const TARGET_COLORS:Record<string,string> = {ability:'#10B981',market:'#F59E0B',interest:'#3B82F6'}
  const TARGET_NAMES:Record<string,string> = {ability:'我擅长',market:'公司需要',interest:'我喜欢'}
  const [disabled, setDisabled] = useState<Set<string>>(new Set())
  const [customs, setCustoms] = useState<any[]>([])
  const [showAdd, setShowAdd] = useState(false); const [newName, setNewName] = useState(''); const [newKW, setNewKW] = useState(''); const [newTarget, setNewTarget] = useState('ability')

  const load = () => {
    api.getResumeProfile().then(p => {
      const a=p.ability_profile; const i=p.interest_profile
      setCustoms([...(a?.custom_dims||[]).map((d:any)=>({...d,target:'ability'})),...(i?.custom_dims||[]).map((d:any)=>({...d,target:'interest'}))])
      setDisabled(new Set([...(a?.dim_disabled||[]),...(i?.dim_disabled||[])]))
    }).catch(()=>{})
  }
  useEffect(()=>{load()},[])

  const toggleDim = async (name:string, t:string) => { await api.toggleDim(name, t); load() }
  const delCustom = async (name:string, t:string) => { await api.removeCustomDim(name, t); load() }
  const addCustom = async () => {
    if(!newName.trim()||!newKW.trim()) return
    const kw=newKW.split(/[,，]/).map((s:string)=>s.trim()).filter(Boolean)
    if(newTarget==='interest') await api.updateInterestProfile({custom_dims:[{name:newName.trim(),keywords:kw}]} as any)
    else await api.updateAbilityProfile({custom_dims:[{name:newName.trim(),keywords:kw}]} as any)
    setShowAdd(false); setNewName(''); setNewKW(''); load()
  }

  return (
    <div className="bg-[#1E293B]/40 border border-white/5 rounded-xl overflow-hidden mb-3">
      <button onClick={()=>setOpen(!open)} className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-gray-400 hover:text-gray-200 transition-colors">
        <span className="flex items-center gap-2"><SlidersHorizontal className="w-3.5 h-3.5"/>评分标准 · {12+customs.length}项{customs.length>0?`（${customs.length}自定义）`:'' }</span>
        {open?<ChevronUp className="w-3.5 h-3.5"/>:<ChevronDown className="w-3.5 h-3.5"/>}
      </button>
      {open&&(
        <div className="px-4 pb-4 space-y-4 border-t border-white/5 pt-3">
          {['ability','market','interest'].map(target=>{
            const items=[...STANDARD.filter(d=>d.target===target),...customs.filter(c=>c.target===target)]
            const color=TARGET_COLORS[target]
            return <div key={target}>
              <div className="text-[11px] font-semibold mb-2 flex items-center gap-2" style={{color}}>
                <span className="w-1.5 h-1.5 rounded-full" style={{backgroundColor:color}}/>
                {TARGET_NAMES[target]}
                <span className="font-normal text-gray-600 text-[10px]">{target==='ability'?'简历 vs JD · 我能胜任吗':target==='market'?'公司角度 · 会录用我吗':'偏好 vs 岗位 · 我想去吗'}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {items.map(item=>{
                  const isDisabled=disabled.has(item.dim||item.name)
                  return <span key={item.dim||item.name} title={isDisabled?'已禁用，点击启用':item.name}
                    onClick={() => item.dim ? toggleDim(item.dim, target) : delCustom(item.name, target)}
                    className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] cursor-pointer transition-all border
                      ${isDisabled ? 'bg-transparent text-gray-700 border-gray-800 line-through' :
                        item.dim ? 'bg-white/5 text-gray-300 border-white/10 hover:border-white/20 hover:bg-white/10' :
                        'bg-[#10B981]/10 text-[#10B981] border-[#10B981]/20 hover:border-[#10B981]/40'}`}>
                    {(item as any).icon||'⭐'} {item.label||item.name}
                    {isDisabled&&<span className="text-[8px] text-gray-700">禁用</span>}
                    {!item.dim&&<button onClick={e=>{e.stopPropagation();delCustom(item.name,target)}} className="text-red-500/30 hover:text-red-400 ml-0.5">×</button>}
                  </span>
                })}
              </div>
            </div>
          })}
          {!showAdd?(
            <button onClick={()=>setShowAdd(true)} className="text-[10px] text-[#10B981]/60 hover:text-[#10B981] border border-dashed border-white/10 rounded-lg px-3 py-1.5 w-full text-center transition-colors">
              + 添加自定义评分项
            </button>
          ):(
            <div className="flex gap-2 items-center bg-[#0B1120] rounded-lg p-2">
              <select value={newTarget} onChange={e=>setNewTarget(e.target.value)} className="bg-black/20 border border-white/10 rounded px-2 py-1.5 text-[10px] text-white w-20 flex-shrink-0">
                <option value="ability">我擅长</option><option value="market">公司需要</option><option value="interest">我喜欢</option>
              </select>
              <input value={newName} onChange={e=>setNewName(e.target.value)} placeholder="名称" className="flex-1 bg-black/20 border border-white/10 rounded px-2 py-1.5 text-[10px] text-white placeholder:text-gray-600"/>
              <input value={newKW} onChange={e=>setNewKW(e.target.value)} placeholder="关键词(逗号分隔)" className="flex-1 bg-black/20 border border-white/10 rounded px-2 py-1.5 text-[10px] text-white placeholder:text-gray-600"/>
              <button onClick={addCustom} className="text-[10px] px-3 py-1.5 bg-[#10B981] hover:bg-[#059669] text-white rounded font-medium transition-colors flex-shrink-0">保存</button>
            </div>
          )}
          <p className="text-[9px] text-gray-600 leading-relaxed">点击维度可<span className="text-gray-400">禁用/启用</span>，自定义维度可<span className="text-red-400">删除</span>。禁用后该维度不参与评分。配置对所有岗位生效。</p>
        </div>
      )}
    </div>
  )
}

function loadWeights() {
  try { const raw = localStorage.getItem('jm_weights'); if (raw) { const w = JSON.parse(raw); return { w1: w.w1 ?? 40, w2: w.w2 ?? 30, w3: w.w3 ?? 30, threshold: w.threshold ?? 60 } } } catch {}
  return { w1: 40, w2: 30, w3: 30, threshold: 60 }
}
function saveWeights(w: object) { localStorage.setItem('jm_weights', JSON.stringify(w)) }

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
  const setW1 = (v: number) => { const remain = 100 - v; const w2n = Math.min(remain, weights.w2); const w = { ...weights, w1: v, w2: w2n, w3: 100 - v - w2n }; setWeights(w); saveWeights(w) }
  const setW2 = (v: number) => { const remain = 100 - v; const w1n = Math.min(remain, weights.w1); const w = { ...weights, w2: v, w1: w1n, w3: 100 - v - w1n }; setWeights(w); saveWeights(w) }
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
      const data = await api.getFeatured({ page: p, page_size: 10, min_score: weights.threshold, type, industry, city, w1: weights.w1, w2: weights.w2, w3: weights.w3 })
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
            <span className="flex items-center gap-2"><SlidersHorizontal className="w-4 h-4" />权重 · 我擅长{weights.w1}% 公司需要{weights.w2}% 我喜欢{weights.w3}%</span>
            {showWeights ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {showWeights && (
            <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div><div className="flex justify-between text-gray-400 mb-1"><span>我擅长</span><span className="text-green-400 font-bold">{weights.w1}%</span></div>
                  <input type="range" min={10} max={70} value={weights.w1} onChange={e => setW1(Number(e.target.value))} className="w-full accent-green-500 h-1.5" />
                  <span className="text-[10px] text-gray-600">自评：我能胜任吗</span></div>
                <div><div className="flex justify-between text-gray-400 mb-1"><span>公司需要</span><span className="text-orange-400 font-bold">{weights.w2}%</span></div>
                  <input type="range" min={10} max={70} value={weights.w2} onChange={e => setW2(Number(e.target.value))} className="w-full accent-orange-500 h-1.5" />
                  <span className="text-[10px] text-gray-600">他评：公司会要我吗</span></div>
                <div><div className="flex justify-between text-gray-400 mb-1"><span>我喜欢</span><span className="text-blue-400 font-bold">{weights.w3}%</span></div>
                  <input type="range" min={10} max={70} value={weights.w3} onChange={e => { const v=Number(e.target.value); const w={...weights,w3:v,w1:Math.min(100-v,weights.w1)}; w.w2=100-w.w1-w.w3; setWeights(w);saveWeights(w) }} className="w-full accent-blue-500 h-1.5" />
                  <span className="text-[10px] text-gray-600">偏好：我想去吗</span></div>
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

        {/* 评分标准配置（可折叠） */}
        <ScoringStandards />

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
