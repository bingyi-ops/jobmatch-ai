import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Phone, MessageSquare, MoreHorizontal, ExternalLink, Edit2 } from 'lucide-react'
import { Application, ApplicationStatus } from '../types'
import { api } from '../api/client'

interface Props {
  applications: Application[]
  onUpdate: () => void
}

const STATUS_CONFIG: Record<ApplicationStatus, { label: string; color: string; bg: string; border: string }> = {
  applied: { label: '已投递', color: 'text-blue-400', bg: 'bg-blue-500/5', border: 'border-blue-500/20' },
  interviewing: { label: '面试中', color: 'text-orange-400', bg: 'bg-orange-500/5', border: 'border-orange-500/20' },
  offer: { label: 'Offer', color: 'text-green-400', bg: 'bg-green-500/5', border: 'border-green-500/20' },
  rejected: { label: '已拒绝', color: 'text-gray-500', bg: 'bg-gray-500/5', border: 'border-gray-500/20' },
}

export default function ApplicationKanban({ applications, onUpdate }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null)
  const [notes, setNotes] = useState<any>({})

  const columns: ApplicationStatus[] = ['applied', 'interviewing', 'offer', 'rejected']

  const handleStatusChange = async (appId: number, newStatus: string) => {
    await api.updateApplication(appId, { status: newStatus })
    onUpdate()
  }

  const startEditing = (app: Application) => {
    setEditingId(app.id)
    setNotes(app.notes || {})
  }

  const saveNotes = async (appId: number) => {
    await api.updateApplication(appId, { notes })
    setEditingId(null)
    onUpdate()
  }

  const grouped = columns.reduce((acc, col) => {
    acc[col] = applications.filter(a => a.status === col)
    return acc
  }, {} as Record<string, Application[]>)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {columns.map(col => {
        const cfg = STATUS_CONFIG[col]
        const apps = grouped[col] || []
        return (
          <div key={col} className={`${cfg.bg} border ${cfg.border} rounded-xl p-3 min-h-[200px]`}>
            <div className={`flex items-center justify-between mb-3 ${cfg.color}`}>
              <span className="text-sm font-semibold">{cfg.label}</span>
              <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full">{apps.length}</span>
            </div>
            <div className="space-y-2">
              {apps.map(app => (
                <div key={app.id} className="bg-[#0B1120]/60 rounded-lg p-3 border border-white/5">
                  <div className="flex items-start justify-between mb-1">
                    <Link to={`/jobs/${app.job_id}`} className="text-sm font-medium text-[#60A5FA] hover:text-[#93C5FD]">
                      {app.job_title}
                    </Link>
                    <div className="flex gap-0.5">
                      {col !== 'applied' && (
                        <button onClick={() => handleStatusChange(app.id, 'applied')}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 hover:bg-blue-500/20">退回</button>
                      )}
                      {col !== 'interviewing' && (
                        <button onClick={() => handleStatusChange(app.id, 'interviewing')}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 hover:bg-orange-500/20">面试</button>
                      )}
                      {col !== 'offer' && (
                        <button onClick={() => handleStatusChange(app.id, 'offer')}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 hover:bg-green-500/20">Offer</button>
                      )}
                      {col !== 'rejected' && (
                        <button onClick={() => handleStatusChange(app.id, 'rejected')}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-gray-500/10 text-gray-400 hover:bg-gray-500/20">拒</button>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mb-1">{app.job_company}</p>
                  <a href={app.job_source_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-gray-600 hover:text-gray-400 flex items-center gap-1 mb-1">
                    <ExternalLink className="w-3 h-3" /> 原文
                  </a>

                  {/* Notes preview / editor */}
                  {editingId === app.id ? (
                    <div className="space-y-2 mt-2 pt-2 border-t border-white/5">
                      <input type="datetime-local" value={notes.interview_time || ''} onChange={e => setNotes({...notes, interview_time: e.target.value})}
                        className="w-full text-xs bg-[#1E293B] border border-white/10 rounded p-1.5 text-white" />
                      <input type="text" value={notes.hr_contact || ''} onChange={e => setNotes({...notes, hr_contact: e.target.value})}
                        placeholder="HR联系方式" className="w-full text-xs bg-[#1E293B] border border-white/10 rounded p-1.5 text-white" />
                      <textarea value={notes.interview_notes || ''} onChange={e => setNotes({...notes, interview_notes: e.target.value})}
                        placeholder="面试心得..." rows={2} className="w-full text-xs bg-[#1E293B] border border-white/10 rounded p-1.5 text-white resize-none" />
                      <div className="flex gap-2">
                        <button onClick={() => saveNotes(app.id)} className="text-xs px-3 py-1 bg-[#10B981] text-white rounded">保存</button>
                        <button onClick={() => setEditingId(null)} className="text-xs px-3 py-1 bg-white/10 text-gray-400 rounded">取消</button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-gray-600 space-y-0.5">
                      {app.notes?.interview_time && (
                        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(app.notes.interview_time).toLocaleString('zh-CN')}</span>
                      )}
                      {app.notes?.hr_contact && (
                        <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {app.notes.hr_contact}</span>
                      )}
                      {app.notes?.interview_notes && (
                        <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {app.notes.interview_notes.slice(0, 30)}{(app.notes.interview_notes?.length || 0) > 30 ? '...' : ''}</span>
                      )}
                      <button onClick={() => startEditing(app)} className="flex items-center gap-1 text-gray-500 hover:text-[#10B981] pt-1">
                        <Edit2 className="w-3 h-3" /> 备注
                      </button>
                    </div>
                  )}
                </div>
              ))}
              {apps.length === 0 && (
                <div className="text-center py-8 text-gray-600 text-sm">
                  <MoreHorizontal className="w-6 h-6 mx-auto mb-1 opacity-30" />
                  暂无
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
