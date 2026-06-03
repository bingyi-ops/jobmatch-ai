import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer } from 'recharts'

interface Props {
  userSkills: string[]
  jdSkills: string[]
  userLabel?: string
  jdLabel?: string
  compact?: boolean
}

/** 标准化技能名 → 权重映射（常见技能关键词聚类） */
const SKILL_CATEGORIES: Record<string, string[]> = {
  '编程语言': ['python', 'java', 'javascript', 'typescript', 'go', 'c++', 'rust', 'scala'],
  '数据分析': ['sql', 'excel', 'tableau', 'r', 'spark', 'hadoop', 'pandas', 'numpy'],
  '机器学习': ['机器学习', '深度学习', 'tensorflow', 'pytorch', 'nlp', 'cv', '推荐系统', '强化学习'],
  '前端开发': ['react', 'vue', 'angular', 'css', 'html', 'webpack', 'node.js', 'flutter'],
  '后端开发': ['微服务', 'docker', 'kubernetes', 'redis', 'mysql', 'mongodb', 'kafka', 'spring'],
  '产品能力': ['需求分析', 'prd', '原型设计', 'axure', 'ab测试', '用户研究', '竞品分析', '项目管理'],
  '运维/DevOps': ['ci/cd', 'jenkins', 'linux', 'ansible', 'terraform', 'prometheus', 'nginx', 'git'],
  '软技能': ['沟通', '团队协作', '项目管理', '演讲', '领导力', '时间管理', '问题解决', '创新思维'],
}

export default function SkillsRadarCompare({ userSkills, jdSkills, userLabel = '你', jdLabel = '岗位要求', compact = false }: Props) {
  const userSet = new Set(userSkills.map(s => s.toLowerCase().trim()))
  const jdSet = new Set(jdSkills.map(s => s.toLowerCase().trim()))

  // 将技能映射到分类维度
  const data = Object.entries(SKILL_CATEGORIES).map(([category, keywords]) => {
    const userHits = keywords.filter(k => userSet.has(k) || [...userSet].some(s => s.includes(k) || k.includes(s))).length
    const jdHits = keywords.filter(k => jdSet.has(k) || [...jdSet].some(s => s.includes(k) || k.includes(s))).length
    const max = keywords.length
    return {
      category,
      [userLabel]: Math.round((userHits / max) * 100),
      [jdLabel]: Math.round((jdHits / max) * 100),
    }
  }).filter(d => d[userLabel] > 0 || d[jdLabel] > 0)

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        暂无足够数据生成技能雷达对比
      </div>
    )
  }

  return (
    <div className={compact ? 'h-48' : 'h-64'}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%">
          <PolarGrid stroke="#334155" strokeWidth={0.5} />
          <PolarAngleAxis
            dataKey="category"
            tick={{ fill: '#94A3B8', fontSize: compact ? 10 : 12 }}
            tickLine={false}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name={userLabel}
            dataKey={userLabel}
            stroke="#10B981"
            fill="#10B981"
            fillOpacity={0.2}
            strokeWidth={2}
          />
          <Radar
            name={jdLabel}
            dataKey={jdLabel}
            stroke="#60A5FA"
            fill="#60A5FA"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Legend
            wrapperStyle={{ fontSize: compact ? 10 : 12 }}
            iconType="circle"
            iconSize={compact ? 6 : 8}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
