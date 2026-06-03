import { Link } from 'react-router-dom'
import { Layers } from 'lucide-react'

interface Props {
  jobs: any[]
  loading?: boolean
}

export default function SimilarJobs({ jobs, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-white/10 rounded w-1/4" />
          <div className="flex gap-3 overflow-hidden">
            {[1, 2, 3].map(i => (
              <div key={i} className="w-40 h-24 bg-white/5 rounded-lg flex-shrink-0" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!jobs || jobs.length === 0) return null

  return (
    <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
        <Layers className="w-4 h-4 text-[#10B981]" />
        相似岗位推荐
      </h3>

      <div className="flex gap-3 overflow-x-auto pb-2 snap-x"
        style={{ scrollSnapType: 'x mandatory' }}>
        {jobs.map((job: any) => (
          <Link
            key={job.id}
            to={`/jobs/${job.id}`}
            className="flex-shrink-0 w-40 bg-[#0B1120]/60 border border-white/5 rounded-lg p-3 hover:border-[#10B981]/20 hover:scale-[1.02] transition-all snap-start"
          >
            <p className="text-xs font-medium text-[#60A5FA] line-clamp-2 mb-1">{job.title}</p>
            <p className="text-[10px] text-gray-500 mb-1.5">{job.company}</p>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-gray-600">{job.city}</span>
              {job.overlap != null && job.overlap >= 60 ? (
                <span className="text-[10px] text-[#10B981] font-medium">匹配 {Math.round(job.overlap)}</span>
              ) : job.overlap != null ? (
                <span className="text-[10px] text-gray-600">低匹配</span>
              ) : (
                <span className="text-[10px] text-gray-700" title="上传简历后可查看匹配度">未匹配</span>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
