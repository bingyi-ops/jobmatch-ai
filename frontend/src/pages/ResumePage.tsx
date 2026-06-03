import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { ResumeProfile } from '../types'
import { Upload, FileText, Sparkles, CheckCircle, Loader2, Target, Brain, Shield, RotateCcw } from 'lucide-react'

export default function ResumePage() {
  const [profile, setProfile] = useState<ResumeProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<string | null>(null)
  const [feedbackHistory, setFeedbackHistory] = useState<any[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { loadProfile() }, [])

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
    setUploading(true)
    try {
      const result = await api.uploadResume(file)
      setUploadResult(result.message)
      await loadProfile()
    } catch (e) { setUploadResult('上传失败，请重试') }
    setUploading(false)
  }

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 text-[#10B981] animate-spin" /></div>
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <FileText className="w-5 h-5 text-[#10B981]" />
        简历与画像管理
      </h1>

      {/* Upload section */}
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-2xl p-8 mb-6 text-center">
        {!profile?.has_resume ? (
          <>
            <Upload className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">上传你的简历</h2>
            <p className="text-gray-500 mb-6 text-sm max-w-sm mx-auto">
              支持 PDF / Word 格式，AI 会自动提取你的三圈画像并匹配所有岗位
            </p>
            <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx" onChange={handleUpload} className="hidden" />
            <button onClick={() => fileInputRef.current?.click()}
              className="px-6 py-3 bg-[#10B981] text-white rounded-xl font-medium hover:bg-[#059669] transition-colors inline-flex items-center gap-2">
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              {uploading ? '解析中...' : '选择文件上传'}
            </button>
            {uploadResult && (
              <div className="mt-4 p-3 bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg text-sm text-[#10B981]">
                <CheckCircle className="w-4 h-4 inline mr-1" /> {uploadResult}
              </div>
            )}
          </>
        ) : (
          <>
            <div className="flex items-center justify-center gap-2 text-[#10B981] mb-4">
              <CheckCircle className="w-6 h-6" />
              <span className="text-lg font-semibold">简历已解析</span>
            </div>
            <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx" onChange={handleUpload} className="hidden" />
            <button onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">
              {uploading ? <Loader2 className="w-4 h-4 animate-spin inline mr-1" /> : null}
              重新上传
            </button>
          </>
        )}
      </div>

      {/* Profile display */}
      {profile?.has_resume && (
        <div className="space-y-4 mb-6">
          {/* Interest */}
          <div className="bg-[#1E293B]/60 border border-blue-500/20 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-blue-400 flex items-center gap-2 mb-3">
              <Target className="w-4 h-4" /> 我喜欢（兴趣画像）
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.interest_profile?.preferred_industries?.map(s => (
                <span key={s} className="px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full text-xs">{s}</span>
              ))}
              {profile.interest_profile?.preferred_roles?.map(s => (
                <span key={s} className="px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full text-xs">{s}</span>
              ))}
            </div>
          </div>

          {/* Ability */}
          <div className="bg-[#1E293B]/60 border border-green-500/20 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-green-400 flex items-center gap-2 mb-3">
              <Brain className="w-4 h-4" /> 我擅长（能力画像）
            </h3>
            <div className="flex flex-wrap gap-2 mb-2">
              {profile.ability_profile?.skills?.slice(0, 8).map(s => (
                <span key={s} className="px-3 py-1 bg-green-500/10 text-green-300 rounded-full text-xs font-medium">{s}</span>
              ))}
              {profile.ability_profile?.skills && profile.ability_profile.skills.length > 8 && (
                <span className="px-3 py-1 bg-green-500/10 text-green-300 rounded-full text-xs">+{(profile.ability_profile.skills.length - 8)}项</span>
              )}
            </div>
            <p className="text-sm text-gray-500">
              {profile.ability_profile?.education} | {profile.ability_profile?.experience}
            </p>
          </div>

          {/* Deal breakers */}
          <div className="bg-[#1E293B]/60 border border-red-500/20 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-red-400 flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4" /> 不可接受项
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.deal_breakers?.map(s => (
                <span key={s} className="px-3 py-1 bg-red-500/10 text-red-300 rounded-full text-xs">{s}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Feedback history timeline */}
      {feedbackHistory.length > 0 && (
        <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#10B981]" /> 反馈历史 · 偏好演变
            </h3>
            <button className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-400 transition-colors">
              <RotateCcw className="w-3 h-3" /> 重置学习模型
            </button>
          </div>
          <div className="space-y-2">
            {feedbackHistory.slice(0, 8).map((fb: any, i: number) => (
              <div key={fb.id || i} className="flex items-center gap-3 text-sm">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  fb.action === 'saved' ? 'bg-pink-400' : 'bg-gray-500'
                }`} />
                <span className="text-gray-400">{fb.job_title || '未知岗位'}</span>
                <span className="text-gray-600">@ {fb.job_company || '未知公司'}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  fb.action === 'saved' ? 'bg-pink-500/10 text-pink-400' : 'bg-gray-500/10 text-gray-500'
                }`}>
                  {fb.action === 'saved' ? '已保存 ↑' : `已忽略 · ${fb.ignore_reason || '无原因'}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
