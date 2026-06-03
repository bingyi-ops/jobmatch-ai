import { useState } from 'react'
import { api } from '../api/client'
import { X, Link, Loader2, Send, Plus } from 'lucide-react'

const CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京']
const INDUSTRIES = ['互联网', '金融', '制造业', '教育', '医疗', '咨询', '快消', '人工智能']
const REC_TYPES: Record<string, string> = {
  daily_intern: '日常实习', summer_intern: '暑期实习', autumn_recruit: '秋招',
  spring_recruit: '春招', experienced: '社招',
}
const SALARY_OPTIONS = ['10k-20k', '15k-25k', '20k-35k', '25k-40k', '30k-50k', '面议']

interface Props {
  onClose: () => void
  onSuccess?: (data: any) => void
}

export default function CustomSourceModal({ onClose, onSuccess }: Props) {
  const [sourceName, setSourceName] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [city, setCity] = useState('')
  const [salaryRange, setSalaryRange] = useState('')
  const [recruitType, setRecruitType] = useState('experienced')
  const [industry, setIndustry] = useState('互联网')
  const [jdText, setJdText] = useState('')
  const [skillsStr, setSkillsStr] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async () => {
    if (!title || !company || !sourceName) return
    setLoading(true)
    try {
      const skills = skillsStr ? skillsStr.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : []
      const result = await api.addCustomSource({
        title,
        company,
        source_name: sourceName,
        source_url: sourceUrl,
        city,
        salary_range: salaryRange,
        recruitment_type: recruitType,
        industry,
        jd_text: jdText,
        skills,
      })
      setSuccess(true)
      onSuccess?.(result)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  if (success) {
    return (
      <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
        <div className="bg-[#1E293B] border border-white/10 rounded-2xl w-full max-w-md p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-[#10B981]/10 flex items-center justify-center mx-auto mb-3">
            <Link className="w-6 h-6 text-[#10B981]" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">来源添加成功！</h3>
          <p className="text-sm text-gray-400 mb-4">
            「{title}」已纳入岗位库，系统已完成自动匹配
          </p>
          <button onClick={onClose}
            className="px-6 py-2 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors">
            完成
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-[#1E293B] border border-white/10 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Plus className="w-4 h-4 text-[#10B981]" /> 添加自定义来源
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
        </div>

        <div className="p-4 space-y-3">
          <p className="text-xs text-gray-500">输入你发现的岗位信息，AI会自动解析并纳入匹配系统</p>

          {/* Source Info */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">来源名称 *</label>
              <input value={sourceName} onChange={e => setSourceName(e.target.value)}
                placeholder="如：张师兄内推、就业网"
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">来源链接</label>
              <input value={sourceUrl} onChange={e => setSourceUrl(e.target.value)}
                placeholder="可选：网址或内推码"
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50" />
            </div>
          </div>

          {/* Job Info */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">岗位名称 *</label>
              <input value={title} onChange={e => setTitle(e.target.value)}
                placeholder="如：数据分析师"
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">公司名称 *</label>
              <input value={company} onChange={e => setCompany(e.target.value)}
                placeholder="如：字节跳动"
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50" />
            </div>
          </div>

          {/* City & Salary */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">城市</label>
              <select value={city} onChange={e => setCity(e.target.value)}
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50">
                <option value="">不限</option>
                {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">薪资范围</label>
              <select value={salaryRange} onChange={e => setSalaryRange(e.target.value)}
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50">
                <option value="">选择</option>
                {SALARY_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          {/* Type & Industry */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">招聘类型</label>
              <select value={recruitType} onChange={e => setRecruitType(e.target.value)}
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50">
                {Object.entries(REC_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block mb-1">行业</label>
              <select value={industry} onChange={e => setIndustry(e.target.value)}
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-[#10B981]/50">
                {INDUSTRIES.map(ind => <option key={ind} value={ind}>{ind}</option>)}
              </select>
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">技能标签（用逗号分隔）</label>
            <input value={skillsStr} onChange={e => setSkillsStr(e.target.value)}
              placeholder="如：Python, SQL, 机器学习, 数据分析"
              className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#10B981]/50" />
          </div>

          {/* JD Text */}
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">JD描述（可选，帮助AI更好匹配）</label>
            <textarea value={jdText} onChange={e => setJdText(e.target.value)}
              placeholder="粘贴岗位描述内容..."
              rows={3}
              className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-2.5 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-[#10B981]/50" />
          </div>

          <button onClick={handleSubmit}
            disabled={loading || !title || !company || !sourceName}
            className="w-full py-3 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            添加至岗位库
          </button>
        </div>
      </div>
    </div>
  )
}
