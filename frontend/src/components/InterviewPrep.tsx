import { useState } from 'react'
import { Play, Send, ArrowLeft, Sparkles, ThumbsUp, ThumbsDown, X, FileText } from 'lucide-react'

interface Props {
  jobTitle: string
  jdSkills: string[]
  applicationId?: number
  jobId?: number
  onReviewClick?: () => void
}

interface Question {
  id: number
  category: string
  categoryColor: string
  questions: string[]
  tips: string
}

const MOCK_QUESTIONS: Question[] = [
  {
    id: 1, category: '技术能力', categoryColor: 'bg-blue-500/20 text-blue-400',
    questions: ['请介绍你在这个技术栈上的项目经验？', '你如何解决性能优化问题？'],
    tips: '准备STAR法则案例，突出量化成果',
  },
  {
    id: 2, category: '项目经验', categoryColor: 'bg-purple-500/20 text-purple-400',
    questions: ['描述一个你主导的最复杂项目', '项目中遇到的最大挑战是什么？'],
    tips: '准备2-3个完整项目故事，每个控制在3分钟内',
  },
  {
    id: 3, category: '行为面试', categoryColor: 'bg-orange-500/20 text-orange-400',
    questions: ['举一个团队冲突的例子，你如何解决？', '描述一次失败经历和你的反思'],
    tips: '诚实面对不足，展示学习成长过程',
  },
  {
    id: 4, category: '行业认知', categoryColor: 'bg-green-500/20 text-green-400',
    questions: ['你如何看待这个行业的未来趋势？', '我们公司在这个领域的竞争优势是什么？'],
    tips: '提前研究公司产品和竞品，形成独立观点',
  },
]

type MockState = 'idle' | 'interviewing' | 'eval' | 'finished'

export default function InterviewPrep({ jobTitle, jdSkills, applicationId, jobId, onReviewClick }: Props) {
  const [mockState, setMockState] = useState<MockState>('idle')
  const [currentQ, setCurrentQ] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [evaluations, setEvaluations] = useState<{ q: string; a: string; score: number; feedback: string }[]>([])
  const [currentEval, setCurrentEval] = useState<{ score: number; feedback: string } | null>(null)

  const questions = MOCK_QUESTIONS.flatMap(q =>
    q.questions.map((qtext, i) => ({ text: qtext, category: q.category, categoryColor: q.categoryColor, tips: q.tips, id: `${q.id}-${i}` }))
  )

  const startMock = () => {
    setMockState('interviewing')
    setCurrentQ(0)
    setEvaluations([])
    setCurrentEval(null)
  }

  const submitAnswer = () => {
    if (!userAnswer.trim()) return
    // Mock evaluation
    const score = Math.floor(Math.random() * 3) + 3 // 3-5
    const feedbacks = [
      '回答结构清晰，建议增加具体数据支撑',
      '很好的切入点，可以进一步展开技术细节',
      '观点新颖，但需要与岗位JD更紧密结合',
    ]
    const eval_ = { score, feedback: feedbacks[Math.floor(Math.random() * feedbacks.length)] }
    setCurrentEval(eval_)
    setMockState('eval')
  }

  const nextQuestion = () => {
    if (currentEval && questions[currentQ]) {
      setEvaluations([...evaluations, { q: questions[currentQ].text, a: userAnswer, ...currentEval }])
    }
    setUserAnswer('')
    setCurrentEval(null)
    if (currentQ + 1 >= questions.length) {
      setMockState('finished')
    } else {
      setCurrentQ(currentQ + 1)
      setMockState('interviewing')
    }
  }

  // Immersive interview mode
  if (mockState !== 'idle') {
    const totalScore = evaluations.length > 0 ? Math.round(evaluations.reduce((s, e) => s + e.score, 0) / evaluations.length) : '-'

    return (
      <div className="fixed inset-0 z-50 bg-[#0B1120] flex flex-col">
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <button onClick={() => setMockState('idle')} className="text-gray-400 hover:text-white flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> 退出
          </button>
          <span className="text-sm text-gray-400">{mockState === 'finished' ? '面试结束' : `问题 ${currentQ + 1} / ${questions.length}`}</span>
          <span className="text-sm text-[#10B981]">{jobTitle}</span>
        </div>

        {/* Main area */}
        {mockState === 'finished' ? (
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-2xl mx-auto text-center mb-8">
              <Sparkles className="w-12 h-12 text-[#10B981] mx-auto mb-3" />
              <h2 className="text-xl font-bold text-white mb-2">模拟面试完成！</h2>
              <div className="text-3xl font-bold text-[#10B981] mb-2">{totalScore} / 5</div>
              <p className="text-gray-500 text-sm">点击下方查看详细评估</p>
            </div>
            {evaluations.map((e, i) => (
              <div key={i} className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4 mb-3 max-w-2xl mx-auto">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{questions[i]?.category}</span>
                  <span className={`text-sm font-bold ${e.score >= 4 ? 'text-[#10B981]' : e.score >= 3 ? 'text-orange-400' : 'text-red-400'}`}>
                    {e.score} / 5 {e.score >= 4 ? <ThumbsUp className="w-3.5 h-3.5 inline" /> : <ThumbsDown className="w-3.5 h-3.5 inline" />}
                  </span>
                </div>
                <p className="text-sm text-white font-medium mb-1">{e.q}</p>
                <p className="text-xs text-gray-500 mb-2">你的回答：{e.a}</p>
                <p className="text-xs text-[#10B981]">💡 {e.feedback}</p>
              </div>
            ))}
            <div className="text-center mt-6 space-y-3">
              {onReviewClick && (
                <button onClick={onReviewClick}
                  className="flex items-center justify-center gap-2 px-6 py-2.5 mx-auto bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 text-purple-400 rounded-lg font-medium text-sm hover:bg-purple-500/30 transition-colors">
                  <FileText className="w-4 h-4" /> 提交面试复盘总结
                </button>
              )}
              <button onClick={() => setMockState('idle')} className="px-6 py-2 bg-[#10B981] text-white rounded-lg font-medium">
                返回
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-2xl mx-auto">
                {/* Question with typewriter feel */}
                <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-6 mb-4">
                  <div className="flex items-center gap-2 mb-4">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${questions[currentQ]?.categoryColor}`}>
                      {questions[currentQ]?.category}
                    </span>
                    <span className="text-xs text-gray-500">{questions[currentQ]?.tips}</span>
                  </div>
                  <p className="text-white text-lg font-medium leading-relaxed">
                    {questions[currentQ]?.text}
                  </p>
                </div>

                {/* Evaluation (if submitted) */}
                {mockState === 'eval' && currentEval && (
                  <div className="bg-[#10B981]/5 border border-[#10B981]/20 rounded-xl p-4 mb-4 animate-celebrate">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-[#10B981] font-medium">AI 评估</span>
                      <span className="text-lg font-bold text-[#10B981]">{currentEval.score} / 5</span>
                    </div>
                    <p className="text-xs text-gray-300">{currentEval.feedback}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Input area */}
            <div className="border-t border-white/10 p-4">
              {mockState === 'eval' ? (
                <button onClick={nextQuestion}
                  className="w-full py-3 bg-[#10B981] text-white rounded-xl font-medium text-sm hover:bg-[#059669] transition-colors flex items-center justify-center gap-2">
                  {currentQ + 1 >= questions.length ? '查看总结报告' : '下一题 →'}
                </button>
              ) : (
                <div className="max-w-2xl mx-auto flex gap-3">
                  <textarea
                    value={userAnswer}
                    onChange={e => setUserAnswer(e.target.value)}
                    placeholder="输入你的回答..."
                    rows={3}
                    className="flex-1 bg-[#1E293B] border border-white/10 rounded-xl p-3 text-sm text-white resize-none focus:outline-none focus:border-[#10B981]/50"
                    onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) submitAnswer() }}
                  />
                  <button onClick={submitAnswer}
                    disabled={!userAnswer.trim()}
                    className="self-end px-4 py-2.5 bg-[#10B981] text-white rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#059669] transition-colors">
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    )
  }

  // Normal view
  return (
    <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          🎤 面试准备建议
        </h3>
      </div>

      <div className="space-y-3 mb-4">
        {MOCK_QUESTIONS.map(q => (
          <div key={q.id} className="bg-[#0B1120]/60 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${q.categoryColor}`}>{q.category}</span>
              <span className="text-xs text-gray-500">{q.tips}</span>
            </div>
            <ul className="space-y-1">
              {q.questions.map((qs, i) => (
                <li key={i} className="text-xs text-gray-400 flex items-start gap-2">
                  <span className="text-gray-600 mt-0.5">{i + 1}.</span>
                  {qs}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <button onClick={startMock}
        className="w-full py-2.5 bg-gradient-to-r from-[#10B981]/20 to-[#10B981]/10 border border-[#10B981]/30 rounded-xl text-sm text-[#10B981] font-medium hover:bg-[#10B981]/20 transition-colors flex items-center justify-center gap-2">
        <Play className="w-4 h-4" /> 开始模拟面试
      </button>
    </div>
  )
}
