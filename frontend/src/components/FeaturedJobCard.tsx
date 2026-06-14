import { useNavigate } from 'react-router-dom'
import { ExternalLink, Heart, EyeOff, Send, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { JobCard } from '../types'
import DeadlineBadge from './DeadlineBadge'
import IgnoreFeedbackModal from './IgnoreFeedbackModal'
import { useState } from 'react'
import { api } from '../api/client'

interface Props { job: JobCard; onFeedback?: () => void }
const TYPE_LABELS: Record<string, string> = { daily_intern:'日常实习',summer_intern:'暑期实习',autumn_recruit:'秋招',spring_recruit:'春招',experienced:'社招' }
const LABEL_CN: Record<string,string> = {
  skills:'技能匹配', projects:'项目经验', education:'学历层次',
  edu_req:'学历达标', major_match:'专业对口', exp_years:'经验年限',
  duty_coverage:'职责覆盖', stability:'工作稳定',
  city:'城市匹配', industry:'行业匹配', salary:'薪资匹配', role:'岗位方向',
}
const STANDARD = new Set(Object.keys(LABEL_CN))

export default function FeaturedJobCard({ job, onFeedback }: Props) {
  const navigate = useNavigate()
  const [showIgnoreModal, setShowIgnoreModal] = useState(false)
  const [showDetail, setShowDetail] = useState(false)
  const [feedback, setFeedback] = useState(job.feedback)
  const isNew = job.posted_at && Date.now() - new Date(job.posted_at).getTime() < 86400000

  const radarData = [
    { subject:'擅长', value:job.ability_score, fullMark:100 },
    { subject:'需要', value:job.market_score, fullMark:100 },
    { subject:'喜欢', value:job.interest_score, fullMark:100 },
  ]

  const handleSave  = async () => { await api.submitFeedback({ match_record_id:job.id, action:'saved' }); setFeedback({ action:'saved' }); onFeedback?.() }
  const handleIgnore = async (r?:string) => { setShowIgnoreModal(false); await api.submitFeedback({ match_record_id:job.id, action:'ignored', ignore_reason:r }); setFeedback({ action:'ignored', ignore_reason:r }); onFeedback?.() }
  const handleApply  = async () => { await api.createApplication({ job_id:job.job_id, match_record_id:job.id }); navigate('/applications') }

  if (feedback?.action === 'ignored') return null

  const ov=job.overlap_score
  const ovGradient = ov>=80 ? ['#059669','#10B981'] : ov>=60 ? ['#D97706','#F59E0B'] : ['#EA580C','#F97316']
  const r=42; const circum=2*Math.PI*r; const dash=(ov/100)*circum

  const dims=[{l:'擅长',s:job.ability_score,c:'#10B981'},{l:'需要',s:job.market_score,c:'#F59E0B'},{l:'喜欢',s:job.interest_score,c:'#3B82F6'}]

  return (
    <div className="group bg-[#1E293B]/80 border border-white/5 rounded-2xl p-5 hover:border-[#10B981]/20 transition-all duration-300">
      <div className="flex items-start justify-between mb-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {isNew&&<span className="px-1.5 py-0.5 bg-red-500 text-white text-[10px] rounded font-bold">NEW</span>}
            <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-[#93C5FD] hover:text-white font-semibold text-sm flex items-center gap-1 transition-colors">{job.title}<ExternalLink className="w-3 h-3 opacity-50"/></a>
          </div>
          <p className="text-gray-500 text-xs mt-0.5">{job.company} · {job.city} · {job.salary_range}</p>
        </div>
        {job.application_deadline&&<DeadlineBadge deadline={job.application_deadline}/>}
      </div>
      <div className="flex flex-wrap gap-1.5 mb-4">
        <span className="text-[11px] px-2 py-0.5 rounded-md bg-[#10B981]/10 text-[#10B981]">{TYPE_LABELS[job.recruitment_type]||job.recruitment_type}</span>
        <span className="text-[11px] px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-400">{job.industry}</span>
      </div>

      {/* 综合分 + 雷达图 + 三维得分 */}
      <div className="flex items-center gap-3 mb-3">
        {/* 综合分圆圈 */}
        <div className="relative w-[90px] h-[90px] flex-shrink-0">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <defs><linearGradient id={`g${job.job_id}`} x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor={ovGradient[0]}/><stop offset="100%" stopColor={ovGradient[1]}/></linearGradient></defs>
            <circle cx="50" cy="50" r={r} fill="none" stroke="#1E293B" strokeWidth="7"/>
            <circle cx="50" cy="50" r={r} fill="none" stroke={`url(#g${job.job_id})`} strokeWidth="7" strokeDasharray={`${dash} ${circum}`} strokeLinecap="round"/>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[26px] font-extrabold tracking-tight" style={{color:ovGradient[1]}}>{ov}</span>
            <span className="text-[9px] text-gray-500 -mt-1">综合分</span>
          </div>
        </div>

        {/* 三维得分 + 雷达 */}
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <div className="flex flex-col gap-2 flex-shrink-0">
            {dims.map(d=>
              <div key={d.l} className="flex items-center gap-1.5">
                <span className="text-[10px] text-gray-400 w-7">{d.l}</span>
                <div className="w-12 h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{width:`${d.s}%`,backgroundColor:d.c}}/>
                </div>
                <span className="text-[11px] font-bold w-6 text-right" style={{color:d.c}}>{d.s}</span>
              </div>
            )}
          </div>
          <div className="flex-1 h-[100px] min-w-[100px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
                <PolarGrid stroke="#1E293B" strokeWidth={1}/>
                <PolarAngleAxis dataKey="subject" tick={{fontSize:11,fill:'#D1D5DB',fontWeight:700}}/>
                <PolarRadiusAxis domain={[0,100]} tick={false} axisLine={false}/>
                <Radar dataKey="value" stroke="#10B981" fill="#10B981" fillOpacity={0.08} strokeWidth={2}/>
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {job.match_reasons&&<p className="text-[11px] text-gray-500/80 leading-relaxed mb-2 border-t border-white/5 pt-2">{job.match_reasons}</p>}

      <div className="flex items-center justify-between">
        <button onClick={()=>setShowDetail(!showDetail)} className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-gray-400 transition-colors">
          {showDetail?<ChevronUp className="w-3 h-3"/>:<ChevronDown className="w-3 h-3"/>}评分明细
        </button>
        <div className="flex items-center gap-1.5">
          <button onClick={()=>navigate(`/jobs/${job.job_id}`)} className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-gray-300 transition-colors">详情</button>
          <button onClick={handleApply} className="text-xs px-3 py-1.5 bg-[#10B981]/20 hover:bg-[#10B981]/30 rounded-lg text-[#10B981] transition-colors"><Send className="w-3 h-3 inline mr-1"/>投递</button>
          <button onClick={handleSave} className={`text-xs p-1.5 rounded-lg transition-colors ${feedback?.action==='saved'?'text-pink-400 bg-pink-500/10':'text-gray-500 hover:text-pink-400 hover:bg-pink-500/5'}`}><Heart className="w-3.5 h-3.5"/></button>
          <button onClick={()=>setShowIgnoreModal(true)} className="text-xs p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors"><EyeOff className="w-3.5 h-3.5"/></button>
        </div>
      </div>

      {showDetail&&(
        <div className="mt-3 bg-[#0B1120]/80 rounded-xl p-4 space-y-3 border border-white/5">
          <p className="text-[10px] text-gray-500">评分明细 · 鼠标悬停查看打分依据 · 评分标准在简历页配置</p>
          {[{l:'我擅长',sub:(job as any).score_card?.ability?.subs,c:'#10B981',total:job.ability_score},
            {l:'公司需要',sub:(job as any).score_card?.market?.subs,c:'#F59E0B',total:job.market_score},
            {l:'我喜欢',sub:(job as any).score_card?.interest?.subs,c:'#3B82F6',total:job.interest_score}].map(d=>
            <div key={d.l}>
              <div className="flex justify-between text-[11px] mb-1"><span className="text-gray-300 font-semibold">{d.l}</span><span className="font-bold" style={{color:d.c}}>{d.total}/100</span></div>
              {d.sub&&Object.entries(d.sub as Record<string,{score:number;explain:string}>).map(([k,v])=>{
                const isCustom=!STANDARD.has(k)
                return <div key={k} className="flex items-center gap-1.5 mb-1 ml-1">
                  <span className={`text-[10px] w-[64px] flex-shrink-0 truncate ${isCustom?'text-[#10B981]':'text-gray-300'}`}>{isCustom?'⭐':''}{LABEL_CN[k]||k}</span>
                  <div className="flex-1 h-1 bg-white/5 rounded-full"><div className="h-full rounded-full" style={{width:`${Math.max((v.score||0)*10,2)}%`,backgroundColor:d.c}}/></div>
                  <span className="text-[10px] font-bold w-5 text-right flex-shrink-0" style={{color:d.c}}>{v.score||0}</span>
                  <span className="text-[9px] text-gray-600 truncate hidden sm:inline flex-1 min-w-0" title={v.explain}>{(v.explain||'').slice(0,40)}</span>
                </div>
              })}
            </div>
          )}
        </div>
      )}
      {showIgnoreModal&&<IgnoreFeedbackModal onClose={()=>setShowIgnoreModal(false)} onConfirm={handleIgnore}/>}
    </div>
  )
}
