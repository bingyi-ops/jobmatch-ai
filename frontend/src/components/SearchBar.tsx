import { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'

interface Props {
  value: string
  onChange: (v: string) => void
  placeholder?: string
}

export default function SearchBar({ value, onChange, placeholder = '搜索岗位标题、公司名称...' }: Props) {
  const [input, setInput] = useState(value)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    setInput(value)
  }, [value])

  const handleChange = (v: string) => {
    setInput(v)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => onChange(v), 300)
  }

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
      <input
        type="text"
        value={input}
        onChange={e => handleChange(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') { clearTimeout(timerRef.current); onChange(input) } }}
        placeholder={placeholder}
        className="w-full pl-10 pr-8 py-2.5 bg-[#1E293B] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#10B981]/50 focus:ring-1 focus:ring-[#10B981]/30 transition-all"
      />
      {input && (
        <button onClick={() => { setInput(''); onChange('') }} className="absolute right-3 top-1/2 -translate-y-1/2">
          <X className="w-4 h-4 text-gray-500 hover:text-white" />
        </button>
      )}
    </div>
  )
}
