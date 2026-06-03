/** 骨架屏加载组件 */
export function CardSkeleton() {
  return (
    <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4 animate-pulse">
      <div className="flex items-start justify-between mb-3">
        <div className="h-5 w-16 bg-white/10 rounded-full" />
        <div className="flex gap-2">
          <div className="h-5 w-10 bg-white/10 rounded-full" />
          <div className="h-5 w-20 bg-white/10 rounded-full" />
        </div>
      </div>
      <div className="space-y-2 mb-3">
        <div className="h-5 w-3/4 bg-white/10 rounded" />
        <div className="h-4 w-1/3 bg-white/10 rounded" />
      </div>
      <div className="flex gap-2 mb-3">
        <div className="h-5 w-12 bg-white/10 rounded" />
        <div className="h-5 w-20 bg-white/10 rounded" />
        <div className="h-5 w-16 bg-white/10 rounded" />
      </div>
      <div className="space-y-1.5 mb-3">
        <div className="h-3 w-full bg-white/10 rounded" />
        <div className="h-3 w-5/6 bg-white/10 rounded" />
      </div>
      <div className="flex gap-1">
        <div className="h-5 w-14 bg-white/10 rounded" />
        <div className="h-5 w-10 bg-white/10 rounded" />
        <div className="h-5 w-16 bg-white/10 rounded" />
      </div>
    </div>
  )
}

export function FeaturedCardSkeleton() {
  return (
    <div className="bg-[#1E293B]/60 border border-white/5 rounded-xl p-4 animate-pulse">
      <div className="flex gap-4">
        <div className="w-24 h-24 rounded-lg bg-white/10" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-3/4 bg-white/10 rounded" />
          <div className="h-4 w-1/2 bg-white/10 rounded" />
          <div className="h-1.5 w-full bg-white/10 rounded-full" />
          <div className="flex gap-2">
            <div className="h-5 w-12 bg-white/10 rounded" />
            <div className="h-5 w-16 bg-white/10 rounded" />
          </div>
        </div>
      </div>
    </div>
  )
}

export function DetailSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 w-2/3 bg-white/10 rounded" />
      <div className="h-5 w-1/3 bg-white/10 rounded" />
      <div className="flex gap-2">
        <div className="h-6 w-16 bg-white/10 rounded" />
        <div className="h-6 w-20 bg-white/10 rounded" />
        <div className="h-6 w-14 bg-white/10 rounded" />
      </div>
      <div className="space-y-2">
        <div className="h-4 w-full bg-white/10 rounded" />
        <div className="h-4 w-5/6 bg-white/10 rounded" />
        <div className="h-4 w-4/5 bg-white/10 rounded" />
      </div>
    </div>
  )
}

export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  )
}
