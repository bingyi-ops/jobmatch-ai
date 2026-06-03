interface Props {
  deadline: string
}

export default function DeadlineBadge({ deadline }: Props) {
  if (!deadline) return null
  const days = Math.ceil(
    (new Date(deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  )

  let color: string
  let text: string
  if (days <= 0) {
    color = 'bg-red-500/20 text-red-400'
    text = '已过期'
  } else if (days <= 3) {
    color = 'bg-red-500/20 text-red-400 animate-pulse'
    text = `${days}天后截止`
  } else if (days <= 7) {
    color = 'bg-orange-500/20 text-orange-400'
    text = `${days}天后截止`
  } else {
    color = 'bg-green-500/20 text-green-400'
    text = `还有${days}天`
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {text}
    </span>
  )
}
