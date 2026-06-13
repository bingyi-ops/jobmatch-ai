import { useState } from 'react'
import { Bug, Lightbulb, Send, Loader2, CheckCircle, X } from 'lucide-react'
import { api } from '../api/client'

interface Props {
  onClose: () => void
}

export default function FeedbackModal({ onClose }: Props) {
  const [type, setType] = useState<'bug' | 'feature'>('bug')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [contact, setContact] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async () => {
    if (!title.trim() || title.trim().length < 2) return
    if (!description.trim() || description.trim().length < 10) return
    setSubmitting(true)
    try {
      await api.submitUserFeedback({ type, title: title.trim(), description: description.trim(), contact: contact.trim() })
      setDone(true)
    } catch (e) { /* ignore */ }
    setSubmitting(false)
  }

  const canSubmit = title.trim().length >= 2 && description.trim().length >= 10 && !submitting

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#1E293B] border border-white/10 rounded-2xl w-full max-w-md mx-4 shadow-2xl max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[#1E293B] border-b border-white/10 px-5 py-4 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              {done ? (
                <><CheckCircle className="w-5 h-5 text-[#10B981]" /> 感谢反馈</>
              ) : (
                <><Bug className="w-5 h-5 text-[#F59E0B]" /> 反馈与建议</>
              )}
            </h3>
            <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-lg leading-none">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {done ? (
          <div className="p-6 text-center">
            <div className="w-14 h-14 rounded-full bg-[#10B981]/10 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-7 h-7 text-[#10B981]" />
            </div>
            <p className="text-white font-semibold mb-2">反馈已提交</p>
            <p className="text-sm text-gray-400 mb-4">感谢你的宝贵意见，我们会认真评估每一条反馈</p>
            <button onClick={onClose}
              className="px-6 py-2 bg-[#10B981] hover:bg-[#059669] rounded-xl text-sm text-white font-medium transition-colors">
              完成
            </button>
          </div>
        ) : (
          <div className="p-5 space-y-4">
            {/* Type selector */}
            <div>
              <label className="text-[10px] text-gray-500 block mb-2">反馈类型</label>
              <div className="flex gap-2">
                <button onClick={() => setType('bug')}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                    type === 'bug' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                  }`}>
                  <Bug className="w-4 h-4" /> 报告 Bug
                </button>
                <button onClick={() => setType('feature')}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                    type === 'feature' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                  }`}>
                  <Lightbulb className="w-4 h-4" /> 功能建议
                </button>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="text-[10px] text-gray-500 block mb-1.5">标题 <span className="text-red-400">*</span></label>
              <input value={title} onChange={e => setTitle(e.target.value)}
                placeholder={type === 'bug' ? '如：导入岗位后看不到新增的岗位' : '如：希望能一键收藏岗位'}
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-[#10B981]/50" />
            </div>

            {/* Description */}
            <div>
              <label className="text-[10px] text-gray-500 block mb-1.5">详细描述 <span className="text-red-400">*</span></label>
              <textarea value={description} onChange={e => setDescription(e.target.value)}
                rows={4}
                placeholder="请详细描述你遇到的问题或希望添加的功能..."
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg p-3 text-sm text-white placeholder:text-gray-600 resize-none focus:outline-none focus:border-[#10B981]/50" />
            </div>

            {/* Contact (optional) */}
            <div>
              <label className="text-[10px] text-gray-500 block mb-1.5">联系方式 <span className="text-gray-600">（选填）</span></label>
              <input value={contact} onChange={e => setContact(e.target.value)}
                placeholder="邮箱或微信，方便我们联系你确认问题"
                className="w-full bg-[#0B1120] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-[#10B981]/50" />
            </div>

            {/* Actions */}
            <div className="flex gap-2 justify-end pt-2 border-t border-white/5">
              <button onClick={onClose}
                className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">
                取消
              </button>
              <button onClick={handleSubmit} disabled={!canSubmit}
                className="px-6 py-2.5 bg-[#10B981] hover:bg-[#059669] disabled:opacity-40 rounded-lg text-sm text-white font-medium transition-colors flex items-center gap-2">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {submitting ? '提交中...' : '提交反馈'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
