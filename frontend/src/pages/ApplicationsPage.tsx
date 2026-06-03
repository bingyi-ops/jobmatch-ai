import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Application, ResumeProfile } from '../types'
import ApplicationKanban from '../components/ApplicationKanban'
import { Loader2, Inbox, PieChart, BarChart3, TrendingUp, Upload } from 'lucide-react'
import { PieChart as RPieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [hasResume, setHasResume] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => { checkResume() }, [])
  useEffect(() => { if (hasResume) loadData() }, [filter, hasResume])

  const checkResume = async () => {
    try {
      const profile = await api.getResumeProfile()
      setHasResume(profile.has_resume)
    } catch { setHasResume(false) }
    setChecking(false)
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const [appData, statsData] = await Promise.all([
        api.getApplications({ page: 1, page_size: 50, status: filter }),
        api.getAppStats(),
      ])
      setApps(appData.items)
      setStats(statsData)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  if (checking) {
    return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 text-[#10B981] animate-spin" /></div>
  }

  if (!hasResume) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Upload className="w-16 h-16 text-gray-600 mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">上传简历后查看投递管理</h2>
        <p className="text-gray-500 mb-6">投递管理需要你先上传简历并完成岗位匹配</p>
        <Link to="/resume" className="px-6 py-3 bg-[#10B981] text-white rounded-xl font-medium">上传简历</Link>
      </div>
    )
  }

  const statusColors = { applied: '#3B82F6', interviewing: '#F59E0B', offer: '#10B981', rejected: '#6B7280' }
  const statusNames = { applied: '已投递', interviewing: '面试中', offer: 'Offer', rejected: '已拒绝' }

  const pieData = stats?.by_status ? Object.entries(stats.by_status).map(([k, v]) => ({ name: (statusNames as any)[k] || k, value: v, color: (statusColors as any)[k] || '#6B7280' })) : []

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Inbox className="w-5 h-5 text-[#10B981]" />
          我的投递
        </h1>
        <div className="flex items-center gap-4 text-sm">
          {stats && (
            <span className="text-gray-400">共 <span className="text-white font-bold">{stats.total}</span> 个投递</span>
          )}
        </div>
      </div>

      {/* Stats panels */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {/* Pie chart - status distribution */}
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1.5">
              <PieChart className="w-4 h-4" /> 状态分布
            </h3>
            <ResponsiveContainer width="100%" height={160}>
              <RPieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={35} outerRadius={60} dataKey="value" paddingAngle={3}>
                  {pieData.map((entry: any, idx: number) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '8px', fontSize: '12px' }} />
              </RPieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-3 justify-center mt-2">
              {pieData.map((d: any, i: number) => (
                <div key={i} className="flex items-center gap-1 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                  <span className="text-gray-400">{d.name}</span>
                  <span className="text-white font-medium">{d.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bar chart - score distribution */}
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4" /> 匹配度分布
            </h3>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={stats.score_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="cnt" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Weekly trend */}
          <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4" /> 周趋势
            </h3>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={stats.weekly_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="week" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="applied" fill="#3B82F6" radius={[4, 4, 0, 0]} name="投递" />
                <Bar dataKey="offer" fill="#10B981" radius={[4, 4, 0, 0]} name="Offer" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-4">
        {['', 'applied', 'interviewing', 'offer', 'rejected'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-lg text-sm transition-all ${
              filter === s ? 'bg-[#10B981]/20 text-[#10B981] font-medium' : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}>
            {s === '' ? '全部' : statusNames[s as keyof typeof statusNames]}
          </button>
        ))}
      </div>

      {/* Kanban */}
      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 text-[#10B981] animate-spin" /></div>
      ) : apps.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Inbox className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p>还没有投递记录，去精选推荐页看看吧</p>
        </div>
      ) : (
        <ApplicationKanban applications={apps} onUpdate={loadData} />
      )}
    </div>
  )
}
