import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { ResumeProfile } from '../types'
import { Upload, FileText, CheckCircle, Loader2, Sparkles, RotateCcw, Code2, GraduationCap, Briefcase, MapPin, Building2, Search, Plus, X, Save, Edit3, Target, Brain, Shield, DollarSign, Navigation } from 'lucide-react'

interface UploadResult {
  extracted_skills: string[]
  extracted_education: string
  extracted_experience: string
  extracted_roles: string[]
  extracted_industries: string[]
  message: string
}

const EDU_OPTIONS = ['博士', '硕士', '本科', '大专', '其他']
const EXP_OPTIONS = ['5年以上', '3-5年', '1-3年', '1年以下', '应届/实习']
const HOT_INDUSTRIES = ['互联网', '人工智能', '金融科技', '新能源', '医疗健康', '教育', '咨询', '快消', '制造业', '通信']
const HOT_ROLES = ['产品经理', '数据分析师', '算法工程师', '后端开发', '前端开发', '运营', '市场', 'HR', '财务', '销售']
const HOT_CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '苏州', '西安']

// ── 可复用的标签编辑组件 ──
function TagEditor({ label, tags, onAdd, onRemove, placeholder, hotTags, colorClass }: {
  label: string; tags: string[]; onAdd: (v: string) => void; onRemove: (v: string) => void;
  placeholder: string; hotTags?: string[]; colorClass: string;
}) {
  const [input, setInput] = useState('')

  const handleAdd = () => {
    const v = input.trim()
    if (!v || tags.includes(v)) { setInput(''); return }
    onAdd(v); setInput('')
  }

  return (
    <div className="space-y-2">
      <label className="text-xs text-gray-500">{label}</label>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map(t => (
            <span key={t} onClick={() => onRemove(t)}
              className={`px-2.5 py-1 rounded-full text-xs cursor-pointer hover:line-through transition-all ${colorClass}`}>
              {t} <X className="w-3 h-3 inline opacity-50" />
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <input type="text" value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), handleAdd())}
          placeholder={placeholder}
          className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-[#10B981]/40" />
        <button onClick={handleAdd}
          className="px-3 py-1.5 bg-[#10B981]/15 hover:bg-[#10B981]/25 border border-[#10B981]/30 rounded-lg text-[#10B981] text-sm transition-colors">
          <Plus className="w-4 h-4" />
        </button>
      </div>
      {hotTags && hotTags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {hotTags.filter(t => !tags.includes(t)).slice(0, 8).map(t => (
            <button key={t} onClick={() => onAdd(t)}
              className="px-2 py-0.5 bg-white/5 border border-white/10 rounded-full text-[10px] text-gray-500 hover:text-white hover:border-white/20 transition-colors">
              + {t}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ResumePage() {
  const [profile, setProfile] = useState<ResumeProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [feedbackHistory, setFeedbackHistory] = useState<any[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── 简历画像 ──
  const [editingAbility, setEditingAbility] = useState(false)
  const [savingAbility, setSavingAbility] = useState(false)
  const [localSkills, setLocalSkills] = useState<string[]>([])
  const [localEdu, setLocalEdu] = useState('本科')
  const [localMajor, setLocalMajor] = useState('')
  const [localExp, setLocalExp] = useState('1-3年')
  const [localProjects, setLocalProjects] = useState<string[]>([])

  // ── 我的偏好 ──
  const [editingInterest, setEditingInterest] = useState(false)
  const [savingInterest, setSavingInterest] = useState(false)
  const [localCities, setLocalCities] = useState<string[]>([])
  const [localIndustries, setLocalIndustries] = useState<string[]>([])
  const [localRoles, setLocalRoles] = useState<string[]>([])
  const [localSalaryMin, setLocalSalaryMin] = useState<number>(0)

  // ── 子维度权重（默认值从后端同步）──
  const [localDimWeights, setLocalDimWeights] = useState<Record<string,number>>({})
  const [showWeightsEditor, setShowWeightsEditor] = useState(false)

  // ── 不可接受项 ──
  const [editingBreakers, setEditingBreakers] = useState(false)
  const [savingBreakers, setSavingBreakers] = useState(false)
  const [localBreakers, setLocalBreakers] = useState<string[]>([])

  useEffect(() => { loadProfile() }, [])

  useEffect(() => {
    if (!profile?.has_resume) return
    const a = profile.ability_profile
    if (a) {
      setLocalSkills(a.skills || [])
      setLocalEdu(a.education || '本科')
      setLocalMajor(a.major || '')
      setLocalExp(a.experience || '1-3年')
      setLocalProjects(a.projects || [])
    }
    const i = profile.interest_profile
    if (i) {
      setLocalCities(i.preferred_cities || [])
      setLocalIndustries(i.preferred_industries || [])
      setLocalRoles(i.preferred_roles || [])
      setLocalSalaryMin(i.salary_min || 0)
    }
    setLocalBreakers(profile.deal_breakers || [])
  }, [profile])

  const loadProfile = async () => {
    setLoading(true)
    try {
      const p = await api.getResumeProfile()
      setProfile(p)
      if (p.has_resume) {
        const fb = await api.getFeedbackHistory(10)
        setFeedbackHistory(fb)
      }
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true); setUploadResult(null)
    try {
      const result = await api.uploadResume(file)
      setUploading(false)
      if (result.processing) {
        // 后台解析中，不阻塞UI，定时检查
        setUploadResult({ extracted_skills: [], extracted_education: '', extracted_experience: '', extracted_roles: [], extracted_industries: [], message: result.message })
        let attempts = 0
        const check = () => {
          setTimeout(async () => {
            try {
              const p = await api.getResumeProfile()
              if (p.has_resume) {
                setProfile(p)
                setUploadResult({
                  extracted_skills: p.ability_profile?.skills || [],
                  extracted_education: p.ability_profile?.education || '',
                  extracted_experience: p.ability_profile?.experience || '',
                  extracted_roles: p.interest_profile?.preferred_roles || [],
                  extracted_industries: p.interest_profile?.preferred_industries || [],
                  message: `简历解析成功！已提取 ${p.ability_profile?.skills?.length || 0} 项技能`,
                })
                return
              }
              attempts++
              if (attempts < 60) check()
              else setUploadResult(prev => prev ? {...prev, message: '解析时间较长，请手动刷新页面（F5）'} : null)
            } catch { attempts++; if (attempts < 60) check() }
          }, 1500)
        }
        check()
      } else {
        setUploadResult({
          extracted_skills: result.extracted_skills || [],
          extracted_education: result.extracted_education || '',
          extracted_experience: result.extracted_experience || '',
          extracted_roles: result.extracted_roles || [],
          extracted_industries: result.extracted_industries || [],
          message: result.message,
        })
        await loadProfile()
      }
    } catch (e: any) {
      setUploadResult({ extracted_skills: [], extracted_education: '', extracted_experience: '', extracted_roles: [], extracted_industries: [], message: e?.message || '上传失败' })
      setUploading(false)
    }
  }

  // ── 保存函数 ──
  const saveAbility = async () => {
    setSavingAbility(true)
    try {
      await api.updateAbilityProfile({
        skills: localSkills, education: localEdu, major: localMajor,
        experience: localExp, projects: localProjects,
      })
      setProfile(p => p ? {
        ...p, ability_profile: { skills: localSkills, education: localEdu, major: localMajor, experience: localExp, projects: localProjects },
      } : null)
      setEditingAbility(false)
    } catch (e) { console.error(e) }
    setSavingAbility(false)
  }

  const saveInterest = async () => {
    setSavingInterest(true)
    try {
      await api.updateInterestProfile({
        preferred_industries: localIndustries, preferred_roles: localRoles,
        preferred_cities: localCities, salary_min: localSalaryMin,
      })
      setProfile(p => p ? {
        ...p, interest_profile: { preferred_industries: localIndustries, preferred_roles: localRoles, preferred_cities: localCities, salary_min: localSalaryMin },
      } : null)
      setEditingInterest(false)
    } catch (e) { console.error(e) }
    setSavingInterest(false)
  }

  const saveBreakers = async () => {
    setSavingBreakers(true)
    try {
      await api.updateDealBreakers(localBreakers)
      setProfile(p => p ? { ...p, deal_breakers: localBreakers } : null)
      setEditingBreakers(false)
    } catch (e) { console.error(e) }
    setSavingBreakers(false)
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 text-[#10B981] animate-spin" /></div>

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <FileText className="w-5 h-5 text-[#10B981]" />
        简历与画像管理
      </h1>

      {/* ── Upload ── */}
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-2xl p-6 mb-6 text-center">
        {!profile?.has_resume ? (
          <>
            <Upload className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <h2 className="text-base font-semibold text-white mb-2">上传你的简历</h2>
            <p className="text-gray-500 mb-4 text-sm">支持 PDF / Word 格式，AI 自动提取画像</p>
            <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx" onChange={handleUpload} className="hidden" />
            <button onClick={() => fileInputRef.current?.click()}
              className="px-6 py-2.5 bg-[#10B981] text-white rounded-xl font-medium hover:bg-[#059669] transition-colors inline-flex items-center gap-2">
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              {uploading ? '解析中...' : '选择文件上传'}
            </button>
          </>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[#10B981]"><CheckCircle className="w-5 h-5" /><span className="font-semibold">简历已解析</span></div>
            <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx" onChange={handleUpload} className="hidden" />
            <button onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-gray-400 hover:text-white transition-colors">
              {uploading ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : null}重新上传
            </button>
          </div>
        )}
        {uploadResult && (
          <div className={`mt-4 p-3 rounded-lg text-sm text-left ${uploadResult.extracted_skills.length > 0 ? 'bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981]' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
            <CheckCircle className="w-4 h-4 inline mr-1" /> {uploadResult.message}
            {uploadResult.extracted_skills.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                <div className="bg-[#0B1120] rounded-lg p-2"><p className="text-[10px] text-gray-500 mb-1"><Code2 className="w-3 h-3 inline mr-1" />技能</p>
                  <div className="flex flex-wrap gap-1">{uploadResult.extracted_skills.map(s => <span key={s} className="px-1.5 py-0.5 bg-green-500/10 text-green-300 rounded text-[11px]">{s}</span>)}</div>
                </div>
                <div className="bg-[#0B1120] rounded-lg p-2 space-y-0.5">
                  <p className="text-[10px] text-gray-500"><GraduationCap className="w-3 h-3 inline mr-1" />{uploadResult.extracted_education}</p>
                  <p className="text-[10px] text-gray-500"><Briefcase className="w-3 h-3 inline mr-1" />{uploadResult.extracted_experience}</p>
                  <p className="text-[10px] text-gray-500"><Search className="w-3 h-3 inline mr-1" />{uploadResult.extracted_roles.join('、')}</p>
                  <p className="text-[10px] text-gray-500"><Building2 className="w-3 h-3 inline mr-1" />{uploadResult.extracted_industries.join('、')}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {profile?.has_resume && (
        <div className="space-y-4 mb-6">
          {/* ── 卡片 1: 简历画像（我擅长 + 公司需要的数据源）── */}
          <div className="bg-[#1E293B]/60 border border-green-500/20 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-green-400 flex items-center gap-2">
                <Brain className="w-4 h-4" /> 简历画像
              </h3>
              {!editingAbility ? (
                <button onClick={() => setEditingAbility(true)}
                  className="text-xs text-gray-500 hover:text-green-400 transition-colors flex items-center gap-1"><Edit3 className="w-3 h-3" />编辑</button>
              ) : (
                <div className="flex gap-2">
                  <button onClick={() => { setEditingAbility(false); loadProfile() }}
                    className="text-xs text-gray-500 hover:text-white transition-colors">取消</button>
                  <button onClick={saveAbility} disabled={savingAbility}
                    className="text-xs text-[#10B981] hover:text-green-300 transition-colors flex items-center gap-1 disabled:opacity-50">
                    {savingAbility ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}保存
                  </button>
                </div>
              )}
            </div>

            {!editingAbility ? (
              /* 只读模式 */
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-[#0B1120] rounded-lg p-3">
                    <span className="text-gray-500 text-xs">学历层次</span>
                    <p className="text-white">{localEdu}{localMajor ? ` · ${localMajor}` : ''}</p>
                  </div>
                  <div className="bg-[#0B1120] rounded-lg p-3">
                    <span className="text-gray-500 text-xs">经验年限</span>
                    <p className="text-white">{localExp}</p>
                  </div>
                </div>
                <div className="bg-[#0B1120] rounded-lg p-3">
                  <span className="text-gray-500 text-xs">技能 ({localSkills.length}项)</span>
                  <div className="flex flex-wrap gap-1 mt-1">{localSkills.map(s => <span key={s} className="px-2 py-0.5 bg-green-500/10 text-green-300 rounded text-xs">{s}</span>)}</div>
                </div>
                {localProjects.length > 0 && (
                  <div className="bg-[#0B1120] rounded-lg p-3">
                    <span className="text-gray-500 text-xs">项目经历</span>
                    <div className="flex flex-wrap gap-1 mt-1">{localProjects.map(s => <span key={s} className="px-2 py-0.5 bg-cyan-500/10 text-cyan-300 rounded text-xs">{s}</span>)}</div>
                  </div>
                )}
              </div>
            ) : (
              /* 编辑模式 */
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">学历层次</label>
                    <select value={localEdu} onChange={e => setLocalEdu(e.target.value)}
                      className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500/40">
                      {EDU_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">经验年限</label>
                    <select value={localExp} onChange={e => setLocalExp(e.target.value)}
                      className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500/40">
                      {EXP_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">专业方向</label>
                  <input type="text" value={localMajor} onChange={e => setLocalMajor(e.target.value)}
                    placeholder="如：计算机科学、统计学、金融学..."
                    className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-green-500/40" />
                </div>
                <TagEditor label="技能标签" tags={localSkills}
                  onAdd={v => setLocalSkills([...localSkills, v])} onRemove={v => setLocalSkills(localSkills.filter(s => s !== v))}
                  placeholder="如：Python、项目管理..." colorClass="bg-green-500/10 text-green-300"
                  hotTags={['Python','SQL','Java','React','机器学习','数据分析','项目管理','沟通能力']} />
                <TagEditor label="项目经历" tags={localProjects}
                  onAdd={v => setLocalProjects([...localProjects, v])} onRemove={v => setLocalProjects(localProjects.filter(s => s !== v))}
                  placeholder="如：用户画像建模、推荐系统优化..." colorClass="bg-cyan-500/10 text-cyan-300" />
              </div>
            )}
          </div>

          {/* ── 卡片 2: 我的偏好（我喜欢的数据源）── */}
          <div className="bg-[#1E293B]/60 border border-blue-500/20 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-blue-400 flex items-center gap-2">
                <Target className="w-4 h-4" /> 我的偏好
              </h3>
              {!editingInterest ? (
                <button onClick={() => setEditingInterest(true)}
                  className="text-xs text-gray-500 hover:text-blue-400 transition-colors flex items-center gap-1"><Edit3 className="w-3 h-3" />编辑</button>
              ) : (
                <div className="flex gap-2">
                  <button onClick={() => { setEditingInterest(false); loadProfile() }}
                    className="text-xs text-gray-500 hover:text-white transition-colors">取消</button>
                  <button onClick={saveInterest} disabled={savingInterest}
                    className="text-xs text-[#10B981] hover:text-green-300 transition-colors flex items-center gap-1 disabled:opacity-50">
                    {savingInterest ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}保存
                  </button>
                </div>
              )}
            </div>

            {!editingInterest ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-[#0B1120] rounded-lg p-3">
                    <span className="text-gray-500 text-xs flex items-center gap-1"><MapPin className="w-3 h-3" />期望城市</span>
                    <div className="flex flex-wrap gap-1 mt-1">{localCities.length > 0 ? localCities.map(c => <span key={c} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded text-xs">{c}</span>) : <span className="text-gray-600 text-xs">未设置</span>}</div>
                  </div>
                  <div className="bg-[#0B1120] rounded-lg p-3">
                    <span className="text-gray-500 text-xs flex items-center gap-1"><DollarSign className="w-3 h-3" />最低薪资</span>
                    <p className="text-white">{localSalaryMin > 0 ? `${localSalaryMin / 1000}k/月` : <span className="text-gray-600 text-xs">未设置</span>}</p>
                  </div>
                </div>
                <div className="bg-[#0B1120] rounded-lg p-3">
                  <span className="text-gray-500 text-xs">意向行业</span>
                  <div className="flex flex-wrap gap-1 mt-1">{localIndustries.length > 0 ? localIndustries.map(s => <span key={s} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded text-xs">{s}</span>) : <span className="text-gray-600 text-xs">未设置</span>}</div>
                </div>
                <div className="bg-[#0B1120] rounded-lg p-3">
                  <span className="text-gray-500 text-xs">意向岗位</span>
                  <div className="flex flex-wrap gap-1 mt-1">{localRoles.length > 0 ? localRoles.map(s => <span key={s} className="px-2 py-0.5 bg-purple-500/10 text-purple-300 rounded text-xs">{s}</span>) : <span className="text-gray-600 text-xs">未设置</span>}</div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <TagEditor label="期望城市（多选）" tags={localCities}
                  onAdd={v => setLocalCities([...localCities, v])} onRemove={v => setLocalCities(localCities.filter(c => c !== v))}
                  placeholder="如：北京、上海..." colorClass="bg-blue-500/10 text-blue-300" hotTags={HOT_CITIES} />
                <TagEditor label="意向行业（多选）" tags={localIndustries}
                  onAdd={v => setLocalIndustries([...localIndustries, v])} onRemove={v => setLocalIndustries(localIndustries.filter(i => i !== v))}
                  placeholder="如：互联网、人工智能..." colorClass="bg-blue-500/10 text-blue-300" hotTags={HOT_INDUSTRIES} />
                <TagEditor label="意向岗位（多选）" tags={localRoles}
                  onAdd={v => setLocalRoles([...localRoles, v])} onRemove={v => setLocalRoles(localRoles.filter(r => r !== v))}
                  placeholder="如：产品经理、数据分析师..." colorClass="bg-purple-500/10 text-purple-300" hotTags={HOT_ROLES} />
                <div>
                  <label className="text-xs text-gray-500 block mb-1">最低薪资（元/月）</label>
                  <input type="number" value={localSalaryMin || ''} onChange={e => setLocalSalaryMin(Number(e.target.value))}
                    placeholder="如：15000（表示月薪不低于15k）"
                    className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500/40" />
                </div>
              </div>
            )}
          </div>

          {/* ── 卡片 3: 不可接受项 ── */}
          <div className="bg-[#1E293B]/60 border border-red-500/20 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-red-400 flex items-center gap-2">
                <Shield className="w-4 h-4" /> 不可接受项
              </h3>
              {!editingBreakers ? (
                <button onClick={() => setEditingBreakers(true)}
                  className="text-xs text-gray-500 hover:text-red-400 transition-colors flex items-center gap-1"><Edit3 className="w-3 h-3" />编辑</button>
              ) : (
                <div className="flex gap-2">
                  <button onClick={() => { setEditingBreakers(false); loadProfile() }}
                    className="text-xs text-gray-500 hover:text-white transition-colors">取消</button>
                  <button onClick={saveBreakers} disabled={savingBreakers}
                    className="text-xs text-[#10B981] hover:text-green-300 transition-colors flex items-center gap-1 disabled:opacity-50">
                    {savingBreakers ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}保存
                  </button>
                </div>
              )}
            </div>
            {!editingBreakers ? (
              <div className="flex flex-wrap gap-1.5">
                {localBreakers.length > 0 ? localBreakers.map(b => <span key={b} className="px-2.5 py-1 bg-red-500/10 text-red-300 rounded-full text-xs">{b}</span>) : <span className="text-gray-600 text-xs">未设置（无过滤）</span>}
              </div>
            ) : (
              <TagEditor label="" tags={localBreakers}
                onAdd={v => setLocalBreakers([...localBreakers, v])} onRemove={v => setLocalBreakers(localBreakers.filter(b => b !== v))}
                placeholder="如：纯开发岗、24小时on-call、996..." colorClass="bg-red-500/10 text-red-300"
                hotTags={['纯开发岗','24小时on-call','996工作制','大小周','长期出差','无明确晋升路径']} />
            )}
            <p className="text-[10px] text-gray-600 mt-2">命中任意一条的岗位将被一票否决，综合分归零，不出现在精选推荐中</p>
          </div>
        </div>
      )}

      {/* ── 反馈历史 ── */}
      {feedbackHistory.length > 0 && (
        <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4 mb-6">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2 mb-3"><Sparkles className="w-4 h-4 text-[#10B981]" />反馈历史</h3>
          <div className="space-y-2">
            {feedbackHistory.slice(0, 8).map((fb: any, i: number) => (
              <div key={fb.id || i} className="flex items-center gap-3 text-xs">
                <div className={`w-1.5 h-1.5 rounded-full ${fb.action === 'saved' ? 'bg-pink-400' : 'bg-gray-500'}`} />
                <span className="text-gray-400">{fb.job_title}</span>
                <span className="text-gray-600">@{fb.job_company}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] ${fb.action === 'saved' ? 'bg-pink-500/10 text-pink-400' : 'bg-gray-500/10 text-gray-500'}`}>
                  {fb.action === 'saved' ? '已保存' : `已忽略·${fb.ignore_reason || ''}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
