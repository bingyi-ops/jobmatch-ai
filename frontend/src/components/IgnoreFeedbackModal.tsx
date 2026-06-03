import { X, DollarSign, MapPin, Cpu, ThumbsDown } from 'lucide-react'
import type { IgnoreReason } from '../types'

interface Props {
  onClose: () => void
  onConfirm: (reason?: string) => void
}

const OPTIONS: { reason: IgnoreReason; label: string; icon: React.ReactNode; desc: string }[] = [
  { reason: 'salary_too_low', label: '薪资太低', icon: <DollarSign className="w-5 h-5" />, desc: '调整薪资偏好下限' },
  { reason: 'location_mismatch', label: '地点不合适', icon: <MapPin className="w-5 h-5" />, desc: '降低该城市权重' },
  { reason: 'skill_mismatch', label: '技能不匹配', icon: <Cpu className="w-5 h-5" />, desc: '降低该技能簇权重' },
  { reason: 'not_interested', label: '不感兴趣', icon: <ThumbsDown className="w-5 h-5" />, desc: '降低该行业/公司权重' },
]

export default function IgnoreFeedbackModal({ onClose, onConfirm }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-[#1E293B] border border-white/10 rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl animate-celebrate">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">为什么忽略这个岗位？</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <p className="text-sm text-gray-400 mb-4">你的反馈将帮助 AI 优化推荐结果</p>
        <div className="space-y-2">
          {OPTIONS.map(opt => (
            <button
              key={opt.reason}
              onClick={() => onConfirm(opt.reason)}
              className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-[#10B981]/10 hover:border-[#10B981]/30 border border-transparent transition-all text-left group"
            >
              <span className="text-gray-400 group-hover:text-[#10B981] transition-colors">{opt.icon}</span>
              <div>
                <div className="text-sm text-white font-medium">{opt.label}</div>
                <div className="text-xs text-gray-500">{opt.desc}</div>
              </div>
            </button>
          ))}
        </div>
        <button
          onClick={() => onConfirm()}
          className="w-full mt-3 py-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
        >
          跳过（不提供原因）
        </button>
      </div>
    </div>
  )
}
