/**
 * 打分结果展示
 */
function ScoreBar({ label, value, color = 'bg-primary-500' }) {
  const pct = Math.max(0, Math.min(100, value))
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="font-semibold text-gray-900">{pct}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function ListCard({ title, emoji, items, color = 'text-gray-700' }) {
  if (!items || items.length === 0) return null
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h3 className="font-semibold text-gray-800 mb-2">
        {emoji} {title}
      </h3>
      <ul className={`space-y-1.5 text-sm ${color}`}>
        {items.map((it, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-gray-400">•</span>
            <span className="flex-1">{it}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ResourceCard({ r }) {
  const typeColor = {
    网站: 'bg-blue-100 text-blue-700',
    视频: 'bg-red-100 text-red-700',
    书籍: 'bg-yellow-100 text-yellow-700',
    课程: 'bg-green-100 text-green-700',
  }[r.type] || 'bg-gray-100 text-gray-700'

  return (
    <a
      href={r.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block border border-gray-200 rounded-lg p-3 hover:border-primary-400 hover:shadow-sm transition"
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="font-medium text-sm text-gray-800 line-clamp-2">
          {r.title}
        </div>
        <span className={`text-xs px-2 py-0.5 rounded ${typeColor} shrink-0`}>
          {r.type}
        </span>
      </div>
      <p className="text-xs text-gray-500 line-clamp-2">{r.description}</p>
      <div className="text-xs text-primary-600 mt-1 truncate">{r.url}</div>
    </a>
  )
}

export default function ScoreResult({ record }) {
  if (!record) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-400">
        还没有打分结果。左边选简历 + 上方粘招聘信息 → 点击「开始打分」
      </div>
    )
  }

  const { overall_score, dimension_scores, strengths, weaknesses,
    resume_improvements, knowledge_areas, learning_resources } = record.result

  const scoreColor =
    overall_score >= 75 ? 'text-green-600' :
    overall_score >= 60 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="bg-white rounded-xl shadow-sm p-5 space-y-4">
      {/* 总分 */}
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <div className="text-sm text-gray-500">总分</div>
          <div className={`text-4xl font-bold ${scoreColor}`}>
            {overall_score}
            <span className="text-base text-gray-400 ml-1">/ 100</span>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>简历：<span className="text-gray-700">{record.resume_filename}</span></div>
          <div>时间：{new Date(record.created_at).toLocaleString('zh-CN')}</div>
        </div>
      </div>

      {/* 四维分数 */}
      <div className="grid grid-cols-2 gap-4">
        <ScoreBar label="技能匹配" value={dimension_scores.skills} color="bg-blue-500" />
        <ScoreBar label="经验匹配" value={dimension_scores.experience} color="bg-green-500" />
        <ScoreBar label="教育背景" value={dimension_scores.education} color="bg-purple-500" />
        <ScoreBar label="项目匹配" value={dimension_scores.project} color="bg-orange-500" />
      </div>

      {/* 优劣势 */}
      <div className="grid grid-cols-2 gap-3">
        <ListCard title="优势" emoji="✅" items={strengths} />
        <ListCard title="不足" emoji="⚠️" items={weaknesses} />
      </div>

      {/* 简历改进 + 知识领域 */}
      <div className="grid grid-cols-2 gap-3">
        <ListCard title="简历改进建议" emoji="📝" items={resume_improvements} />
        <ListCard title="需强化的知识" emoji="📚" items={knowledge_areas} />
      </div>

      {/* 学习资源 */}
      {learning_resources && learning_resources.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-800 mb-2">🎓 推荐学习资源</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {learning_resources.map((r, i) => (
              <ResourceCard key={i} r={r} />
            ))}
          </div>
        </div>
      )}

      {/* 搜索摘要（可折叠） */}
      {record.search_summary && (
        <details className="bg-gray-50 rounded-lg p-3">
          <summary className="cursor-pointer text-sm font-medium text-gray-700">
            🔍 联网搜索摘要（点击展开）
          </summary>
          <pre className="text-xs text-gray-600 mt-2 whitespace-pre-wrap font-sans">
            {record.search_summary}
          </pre>
        </details>
      )}
    </div>
  )
}
