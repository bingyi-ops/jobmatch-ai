import { Link, useLocation } from 'react-router-dom'
import { Target, FileText, MessageSquare } from 'lucide-react'
import { useState } from 'react'
import FeedbackModal from './FeedbackModal'

const TABS = [
  { path: '/all', label: '全部' },
  { path: '/featured', label: '精选推荐' },
  { path: '/applications', label: '我的投递' },
]

export default function Header() {
  const location = useLocation()
  const [showFeedback, setShowFeedback] = useState(false)
  const currentTab = TABS.find(t => location.pathname.startsWith(t.path))?.path || '/all'

  return (
    <header className="bg-[#1E293B]/60 backdrop-blur border-b border-white/10 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/all" className="flex items-center gap-2 text-white no-underline">
            <Target className="w-6 h-6 text-[#10B981]" />
            <span className="font-bold text-lg">JobMatch AI</span>
            <span className="text-xs text-gray-500 hidden sm:inline">智能求职匹配</span>
          </Link>

          {/* Tabs */}
          <nav className="flex gap-1">
            {TABS.map(tab => (
              <Link
                key={tab.path}
                to={tab.path}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                  currentTab === tab.path
                    ? 'bg-[#10B981]/20 text-[#10B981] font-medium'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {tab.label}
              </Link>
            ))}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            {/* Feedback */}
            <button onClick={() => setShowFeedback(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
              title="反馈与建议">
              <MessageSquare className="w-4 h-4" />
              <span className="hidden sm:inline">反馈</span>
            </button>

            {/* Resume */}
            <Link to="/resume"
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-[#10B981]/10 text-[#10B981] rounded-lg hover:bg-[#10B981]/20 transition-colors">
              <FileText className="w-4 h-4" />
              <span className="hidden sm:inline">简历</span>
            </Link>
          </div>
        </div>
      </div>
      {showFeedback && <FeedbackModal onClose={() => setShowFeedback(false)} />}
    </header>
  )
}
