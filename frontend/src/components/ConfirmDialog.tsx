import { AlertTriangle } from 'lucide-react'

interface Props {
  open: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'info'
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({
  open, title, message, confirmText = '确认', cancelText = '取消',
  variant = 'warning', onConfirm, onCancel,
}: Props) {
  if (!open) return null

  const colors = {
    danger: 'border-red-500/30 bg-red-500/10 text-red-400',
    warning: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400',
    info: 'border-blue-500/30 bg-blue-500/10 text-blue-400',
  }

  const btnColors = {
    danger: 'bg-red-600 hover:bg-red-500',
    warning: 'bg-yellow-600 hover:bg-yellow-500 text-black',
    info: 'bg-blue-600 hover:bg-blue-500',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />
      {/* Dialog */}
      <div className="relative bg-[#1E293B] border border-white/10 rounded-2xl p-6 max-w-sm w-full shadow-2xl animate-in slide-in-from-bottom-4">
        <div className="flex items-start gap-3 mb-4">
          <div className={`p-2 rounded-lg ${colors[variant]}`}>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-white font-semibold mb-1">{title}</h3>
            <p className="text-sm text-gray-400">{message}</p>
          </div>
        </div>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 text-sm text-white rounded-lg transition-colors ${btnColors[variant]}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
