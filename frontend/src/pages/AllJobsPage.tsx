import { useState, useEffect, useMemo } from 'react'
import { api } from '../api/client'
import { Job } from '../types'
import JobCard from '../components/JobCard'
import SearchBar from '../components/SearchBar'
import TwoLevelFilter from '../components/TwoLevelFilter'
import Pagination from '../components/Pagination'
import ImportJobModal from '../components/ImportJobModal'
import { ListSkeleton } from '../components/Skeleton'
import { useToast } from '../components/Toast'
import { Briefcase, Clock, AlertCircle, Plus, ShieldOff } from 'lucide-react'

interface DateGroup {
  label: string
  jobs: Job[]
}

export default function AllJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [platform, setPlatform] = useState('')
  const [type, setType] = useState('')
  const [search, setSearch] = useState('')
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [cleaning, setCleaning] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    setPage(1)
    loadJobs(1)
  }, [platform, type, search])

  const loadJobs = async (p: number) => {
    setLoading(true)
    try {
      const data = await api.getAllJobs({ page: p, page_size: 10, platform, type, search })
      setJobs(data.items)
      setTotal(data.total)
      setPage(p)
      setError('')
    } catch (e) {
      setError('加载岗位失败，请稍后重试')
      toast('error', '岗位数据加载失败')
    }
    setLoading(false)
  }

  const handleImportSuccess = () => {
    setShowImportModal(false)
    setEditingJob(null)
    loadJobs(page)
  }

  const handleEditJob = (job: Job) => {
    setEditingJob(job)
    setShowImportModal(true)
  }

  const handleJobDeleted = () => {
    loadJobs(page)
  }

  const handleCleanup = async () => {
    if (!window.confirm('将自动清理非岗位内容（如新闻早报、科技文章等）。\n此操作不可撤销，是否继续？')) return
    setCleaning(true)
    try {
      const res = await api.rescoreAllJobs()
      toast('success', res.message)
      loadJobs(page)
    } catch (e: any) {
      toast('error', e?.message || '清理失败')
    }
    setCleaning(false)
  }

  // 按日期分组：今天 / 昨天 / 更早
  const groups = useMemo<DateGroup[]>(() => {
    if (!jobs.length) return []
    const now = new Date()
    const todayStr = now.toISOString().slice(0, 10)
    const yday = new Date(now)
    yday.setDate(yday.getDate() - 1)
    const ydayStr = yday.toISOString().slice(0, 10)
    const groupsMap: Record<string, Job[]> = {}
    for (const job of jobs) {
      const d = (job.posted_at || '').slice(0, 10)
      let label = ''
      if (d === todayStr) label = '今天'
      else if (d === ydayStr) label = '昨天'
      else label = d || '未知日期'
      if (!groupsMap[label]) groupsMap[label] = []
      groupsMap[label].push(job)
    }
    // 固定顺序
    const order = ['今天', '昨天']
    const result: DateGroup[] = []
    for (const k of order) {
      if (groupsMap[k]) { result.push({ label: k, jobs: groupsMap[k] }); delete groupsMap[k] }
    }
    for (const k of Object.keys(groupsMap).sort().reverse()) {
      result.push({ label: k, jobs: groupsMap[k] })
    }
    return result
  }, [jobs])

  return (
    <div>
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-[#10B981]" />
            全部岗位
            {total > 0 && (
              <span className="text-sm font-normal text-gray-500 ml-2">
                共 {total} 个岗位
              </span>
            )}
          </h1>
          {/* 快捷统计 + 数据清理 */}
          <div className="hidden sm:flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              按发布时间排序
            </span>
            <button onClick={handleCleanup} disabled={cleaning}
              className="flex items-center gap-1 px-2 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors disabled:opacity-50"
              title="清理非岗位内容（如早报、速递、文章等）">
              <ShieldOff className="w-3.5 h-3.5" />
              {cleaning ? '清理中...' : '清理数据'}
            </button>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex gap-2">
            <div className="flex-1">
              <SearchBar value={search} onChange={v => setSearch(v)} placeholder="搜索岗位标题、公司、如：人力资源、数据分析..." />
            </div>
            <button onClick={() => { setEditingJob(null); setShowImportModal(true) }}
              className="px-3 py-2.5 bg-[#10B981]/80 hover:bg-[#10B981] rounded-lg text-sm text-white font-medium transition-colors flex items-center gap-2 whitespace-nowrap">
              <Plus className="w-4 h-4" />
              导入岗位
            </button>
          </div>
          <TwoLevelFilter
            platform={platform} type={type}
            onPlatformChange={v => setPlatform(v)}
            onTypeChange={v => setType(v)}
            onAddCustom={() => { setEditingJob(null); setShowImportModal(true) }}
          />
        </div>
      </div>

      {/* Loading */}
      {loading && <ListSkeleton count={4} />}

      {/* Error */}
      {!loading && error && (
        <div className="text-center py-20">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 text-red-400/30" />
          <p className="text-red-400/70 mb-3">{error}</p>
          <button onClick={() => loadJobs(page)} className="text-sm px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-300 transition-colors">重试</button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && jobs.length === 0 && (
        <div className="text-center py-20 text-gray-500">
          <Briefcase className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p>暂无岗位，试试调整筛选条件或添加自定义来源</p>
        </div>
      )}

      {/* Time-grouped List */}
      {!loading && !error && groups.map(group => (
        <div key={group.label} className="mb-6">
          {/* 日期分隔线 */}
          <div className="flex items-center gap-3 mb-3">
            <div className="h-px bg-white/10 flex-1" />
            <span className="text-xs text-gray-500 whitespace-nowrap flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              {group.label}
              <span className="text-gray-600">（{group.jobs.length} 个）</span>
            </span>
            <div className="h-px bg-white/10 flex-1" />
          </div>
          <div className="space-y-3">
            {group.jobs.map(job => (
              <JobCard key={job.id} job={job} onEdit={handleEditJob} onDeleted={handleJobDeleted} />
            ))}
          </div>
        </div>
      ))}

      <div className="mt-6">
        <Pagination page={page} total={total} pageSize={10} onChange={loadJobs} />
      </div>

      {showImportModal && (
        <ImportJobModal
          onClose={() => { setShowImportModal(false); setEditingJob(null) }}
          onSuccess={handleImportSuccess}
          editJob={editingJob}
        />
      )}
    </div>
  )
}
