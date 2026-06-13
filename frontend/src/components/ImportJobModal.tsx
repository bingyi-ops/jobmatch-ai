import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useToast } from './Toast'
import { Job } from '../types'
import { Link, Loader2, CheckCircle, AlertCircle, Sparkles, ExternalLink, Plus, Pencil } from 'lucide-react'

const SOURCE_CHANNELS = [
  { value: '官网直投', label: '官网直投', platform: 'official' },
  { value: 'Boss直聘转发', label: 'Boss直聘转发', platform: 'boss_zhipin' },
  { value: '就业网', label: '就业网', platform: 'school_career' },
  { value: '学长内推', label: '学长内推', platform: 'referral' },
  { value: '招聘平台', label: '招聘平台', platform: 'custom' },
  { value: '小红书', label: '小红书', platform: 'xiaohongshu' },
  { value: '公众号', label: '公众号', platform: 'wechat_public' },
  { value: '其他渠道', label: '其他渠道', platform: 'custom' },
]

const CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '西安', '苏州']
const INDUSTRIES = ['互联网', '金融', '制造业', '教育', '医疗', '咨询', '快消', '人工智能', '通信', '能源', '不限']
const REC_TYPES: Record<string, string> = {
  daily_intern: '日常实习', summer_intern: '暑期实习',
  autumn_recruit: '秋招', spring_recruit: '春招', experienced: '社招',
}
const SALARY_OPTIONS = ['面议', '10k-15k', '15k-20k', '15k-25k', '20k-30k', '20k-35k', '25k-40k', '30k-50k', '40k-60k']

interface Props {
  onClose: () => void
  onSuccess: () => void
  editJob?: Job | null
}

export default function ImportJobModal({ onClose, onSuccess, editJob }: Props) {
  const [url, setUrl] = useState('')
  const [jdText, setJdText] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parseError, setParseError] = useState('')
  const [parsed, setParsed] = useState(false)

  // 表单字段
  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [city, setCity] = useState('')
  const [salaryRange, setSalaryRange] = useState('')
  const [recruitType, setRecruitType] = useState('experienced')
  const [industry, setIndustry] = useState('')
  const [skillsStr, setSkillsStr] = useState('')
  const [sourceChannel, setSourceChannel] = useState('其他渠道')
  const [sourceName, setSourceName] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [doneMsg, setDoneMsg] = useState('')
  const { toast } = useToast()

  const isEdit = !!editJob

  // 编辑模式下预填数据
  useEffect(() => {
    if (editJob) {
      setTitle(editJob.title || '')
      setCompany(editJob.company || '')
      setCity(editJob.city || '')
      setSalaryRange(editJob.salary_range || '')
      setRecruitType(editJob.recruitment_type || 'experienced')
      setIndustry(editJob.industry || '')
      setJdText(editJob.jd_text || '')
      setSkillsStr(Array.isArray(editJob.jd_skills) ? editJob.jd_skills.join(', ') : '')
      setSourceName(editJob.custom_source_name || '')
      setUrl(editJob.source_url && !editJob.source_url.startsWith('http') ? '' : (editJob.source_url || ''))
      // 从 source_name 中尝试识别渠道
      const ch = SOURCE_CHANNELS.find(c => (editJob.custom_source_name || '').startsWith(c.value))
      setSourceChannel(ch?.value || '其他渠道')
    }
  }, [editJob])

  // AI 智能解析 JD 文本
  const handleParse = async () => {
    if (!jdText.trim() || jdText.trim().length < 20) {
      setParseError('请先粘贴至少20字的岗位描述文本')
      return
    }
    setParsing(true)
    setParseError('')
    try {
      const res = await api.parseJDFromText(jdText.trim())
      if (res.success && res.data) {
        const d = res.data
        if (d.job_title) setTitle(d.job_title)
        if (d.company) setCompany(d.company)
        if (d.city) setCity(d.city)
        if (d.salary_range) setSalaryRange(d.salary_range)
        if (d.industry) setIndustry(d.industry)
        if (d.skills && d.skills.length > 0) setSkillsStr(d.skills.join(', '))
        if (d.recruitment_type) setRecruitType(d.recruitment_type)
        if (d.job_title && d.company) {
          setSourceName(`${sourceChannel} - ${d.job_title}@${d.company}`)
        }
        setParsed(true)
        toast('success', 'AI 解析完成，请核对并修改信息后确认导入')
      } else {
        setParseError(res.error || 'AI 解析失败，请检查 API 配置或手动填写以下字段')
      }
    } catch (e: any) {
      setParseError(e?.message || '解析请求失败，请手动填写')
    }
    setParsing(false)
  }

  // 确认导入 / 保存编辑
  const handleSubmit = async () => {
    if (!title.trim() || !company.trim()) {
      toast('warning', '岗位名称和公司为必填项')
      return
    }
    setSubmitting(true)
    try {
      const skills = skillsStr
        ? skillsStr.split(/[,，、]/).map((s: string) => s.trim()).filter(Boolean)
        : []

      if (isEdit && editJob) {
        // 编辑模式
        const res = await api.updateJob(editJob.id, {
          title: title.trim(),
          company: company.trim(),
          source_name: sourceName || `${sourceChannel} - ${title.trim()}@${company.trim()}`,
          source_url: url.trim(),
          source_channel: sourceChannel,
          city,
          salary_range: salaryRange,
          recruitment_type: recruitType,
          industry,
          jd_text: jdText.trim(),
          skills,
        })
        setDone(true)
        setDoneMsg(res.message || '岗位更新成功！')
        toast('success', res.message || '岗位更新成功！')
        setTimeout(() => {
          onSuccess()
          onClose()
        }, 1500)
      } else {
        // 新增模式：统一使用 url-import 接口
        const res = await api.importJobFromURL({
          url: url.trim(),
          title: title.trim(),
          company: company.trim(),
          source_channel: sourceChannel,
          source_name: sourceName || `${sourceChannel} - ${title.trim()}@${company.trim()}`,
          city,
          salary_range: salaryRange,
          recruitment_type: recruitType,
          industry,
          jd_text: jdText.trim(),
          skills,
        })

        if (res.success) {
          setDone(true)
          setDoneMsg(res.message || '岗位导入成功！')
          toast('success', res.message || '岗位导入成功！')
          setTimeout(() => {
            onSuccess()
            onClose()
          }, 1500)
        } else {
          toast('warning', '导入失败，请重试')
        }
      }
    } catch (e: any) {
      toast('error', e?.message || '操作失败，请稍后重试')
    }
    setSubmitting(false)
  }

  // 在浏览器中打开链接
  const openInBrowser = () => {
    if (url.trim()) {
      window.open(url.trim(), '_blank', 'noopener,noreferrer')
    }
  }

  // ─── 完成界面 ───
  if (done) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="bg-[#1E293B] border border-white/10 rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl text-center">
          <div className="w-14 h-14 rounded-full bg-[#10B981]/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-7 h-7 text-[#10B981]" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">{isEdit ? '更新成功！' : '导入成功！'}</h3>
          <p className="text-sm text-gray-400 mb-4">{doneMsg}</p>
          <button
            onClick={() => { onSuccess(); onClose() }}
            className="px-6 py-2 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors"
          >
            完成
          </button>
        </div>
      </div>
    )
  }

  // ─── 主界面 ───
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#1E293B] border border-white/10 rounded-2xl w-full max-w-lg mx-4 shadow-2xl max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[#1E293B] border-b border-white/10 px-5 py-4 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              {isEdit ? (
                <><Pencil className="w-5 h-5 text-[#60A5FA]" /> 编辑岗位</>
              ) : (
                <><Plus className="w-5 h-5 text-[#10B981]" /> 导入岗位</>
              )}
            </h3>
            <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-lg leading-none">
              ✕
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {isEdit
              ? '修改岗位信息后保存更新'
              : '填写岗位信息，或粘贴JD文本让AI智能解析'}
          </p>
        </div>

        <div className="p-5 space-y-4">
          {/* 数据来源渠道 - 下拉框 */}
          <div>
            <label className="text-[10px] text-gray-500 block mb-1.5">数据来源渠道 *</label>
            <select
              value={sourceChannel}
              onChange={e => {
                setSourceChannel(e.target.value)
                if (!isEdit) setSourceName(`${e.target.value} - ${title || '岗位'}@${company || '公司'}`)
              }}
              className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50"
            >
              {SOURCE_CHANNELS.map(ch => (
                <option key={ch.value} value={ch.value}>{ch.label}</option>
              ))}
            </select>
          </div>

          {/* 来源备注 */}
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">来源备注（自动生成，可修改）</label>
            <input
              value={sourceName}
              onChange={e => setSourceName(e.target.value)}
              placeholder="如：张师兄内推 - Java开发@字节跳动"
              className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
            />
          </div>

          {/* 参考链接（可选） */}
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">参考链接（可选，用于记录岗位来源）</label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://www.zhipin.com/job_detail/xxx.html"
                className="flex-1 bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
              />
              {url.trim() && (
                <button
                  onClick={openInBrowser}
                  className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
                  title="在浏览器中打开"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* JD文本粘贴 + AI解析 */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[10px] text-gray-500">
                JD描述
                <span className="text-gray-600 ml-1">粘贴从招聘网站复制的岗位描述内容</span>
              </label>
            </div>
            <textarea
              value={jdText}
              onChange={e => { setJdText(e.target.value); setParsed(false); setParseError('') }}
              placeholder="粘贴岗位描述内容...&#10;&#10;例如：&#10;【岗位职责】&#10;1. 负责数据分析平台搭建...&#10;【任职要求】&#10;1. 本科及以上学历..."
              rows={5}
              className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-3 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-[#10B981]/50"
            />
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleParse}
                disabled={parsing || jdText.trim().length < 20}
                className="px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] hover:from-blue-500 hover:to-purple-500 disabled:opacity-40 rounded-lg text-sm text-white font-medium transition-all flex items-center gap-2"
              >
                {parsing ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> AI解析中...</>
                ) : (
                  <><Sparkles className="w-4 h-4" /> AI智能解析</>
                )}
              </button>
              {parsed && (
                <span className="text-xs text-green-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> 解析完成，请核对
                </span>
              )}
            </div>
            {parseError && (
              <div className="mt-2 p-2 rounded-lg text-xs bg-red-500/10 border border-red-500/20 text-red-400 flex items-start gap-2">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <span>{parseError}</span>
              </div>
            )}
          </div>

          {/* 解析/手动填写字段 */}
          <div className="border-t border-white/5 pt-4">
            <p className="text-xs text-gray-500 mb-3">
              {parsed ? '以下信息由AI自动填充，请核对修改：' : '请填写以下岗位信息：'}
            </p>

            {/* 岗位名 + 公司 */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-[10px] text-gray-500 block mb-1">岗位名称 *</label>
                <input
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="如：Java后端开发工程师"
                  className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
                />
              </div>
              <div>
                <label className="text-[10px] text-gray-500 block mb-1">公司名称 *</label>
                <input
                  value={company}
                  onChange={e => setCompany(e.target.value)}
                  placeholder="如：字节跳动"
                  className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
                />
              </div>
            </div>

            {/* 城市 + 薪资 */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-[10px] text-gray-500 block mb-1">工作城市</label>
                <div className="flex gap-1">
                  <select
                    value={city}
                    onChange={e => setCity(e.target.value)}
                    className="flex-1 bg-[#0B1120] border border-white/10 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50"
                  >
                    <option value="">选择城市</option>
                    {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <input
                    value={city && !CITIES.includes(city) ? city : ''}
                    onChange={e => setCity(e.target.value)}
                    placeholder="其他"
                    className="w-16 bg-[#0B1120] border border-white/10 rounded-lg px-2 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
                  />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-gray-500 block mb-1">薪资范围</label>
                <div className="flex gap-1">
                  <select
                    value={SALARY_OPTIONS.includes(salaryRange) ? salaryRange : ''}
                    onChange={e => setSalaryRange(e.target.value)}
                    className="flex-1 bg-[#0B1120] border border-white/10 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50"
                  >
                    <option value="">选择</option>
                    {SALARY_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <input
                    value={salaryRange && !SALARY_OPTIONS.includes(salaryRange) ? salaryRange : ''}
                    onChange={e => setSalaryRange(e.target.value)}
                    placeholder="自定义"
                    className="w-20 bg-[#0B1120] border border-white/10 rounded-lg px-2 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
                  />
                </div>
              </div>
            </div>

            {/* 招聘类型 + 行业 */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-[10px] text-gray-500 block mb-1">招聘类型</label>
                <select
                  value={recruitType}
                  onChange={e => setRecruitType(e.target.value)}
                  className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50"
                >
                  {Object.entries(REC_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-gray-500 block mb-1">所属行业</label>
                <select
                  value={industry}
                  onChange={e => setIndustry(e.target.value)}
                  className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50"
                >
                  <option value="">选择</option>
                  {INDUSTRIES.map(ind => <option key={ind} value={ind}>{ind}</option>)}
                </select>
              </div>
            </div>

            {/* 技能标签 */}
            <div className="mb-4">
              <label className="text-[10px] text-gray-500 block mb-1">技能标签（逗号分隔）</label>
              <input
                value={skillsStr}
                onChange={e => setSkillsStr(e.target.value)}
                placeholder="如：Python, SQL, 机器学习, 数据分析"
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50"
              />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 justify-end pt-2 border-t border-white/5">
            <button
              onClick={onClose}
              className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-gray-400 hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !title.trim() || !company.trim()}
              className="px-6 py-2.5 bg-[#10B981] hover:bg-[#059669] disabled:opacity-40 rounded-lg text-sm text-white font-medium transition-colors flex items-center gap-2"
            >
              {submitting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> {isEdit ? '保存中...' : '导入中...'}</>
              ) : (
                <>{isEdit ? '保存修改' : '确认导入'}</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
