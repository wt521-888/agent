/**
 * 打分结果展示
 */
import { useState } from 'react'
import axios from 'axios'

const API = '/api'

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


/**
 * 一键优化简历弹窗
 * - 展示 LLM 重写后的纯文本
 * - 提供「下载新文件」「复制文本」「查看备份」三个动作
 */
function ModifyResumeModal({ open, loading, data, error, onClose, onRetry }) {
  const [copied, setCopied] = useState(false)
  if (!open) return null

  const handleCopy = async () => {
    if (!data?.modified_content) return
    try {
      await navigator.clipboard.writeText(data.modified_content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // 兜底：选中文本
      const ta = document.createElement('textarea')
      ta.value = data.modified_content
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-800">
            📝 一键优化简历
            <span className="text-xs text-gray-500 font-normal ml-2">
              原文件已备份，未被修改
            </span>
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading && (
            <div className="py-16 text-center text-gray-500">
              <div className="inline-block animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full mb-3" />
              <div>正在调用 LLM 重写简历，请稍候…</div>
            </div>
          )}

          {error && !loading && (
            <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
              <div className="mt-2">
                <button
                  onClick={onRetry}
                  className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded"
                >
                  重试
                </button>
              </div>
            </div>
          )}

          {data && !loading && !error && (
            <>
              {/* 应用了哪些建议 */}
              {data.applied_improvements?.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-amber-800 mb-1">
                    ✨ 已应用 {data.applied_improvements.length} 条改进建议
                  </div>
                  <ul className="text-xs text-amber-700 space-y-0.5 list-disc pl-5">
                    {data.applied_improvements.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 文件信息 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-600">
                <div className="bg-gray-50 rounded p-2">
                  <span className="text-gray-400">原文件：</span>
                  <span className="font-mono">{data.original_filename}</span>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <span className="text-gray-400">备份为：</span>
                  <span className="font-mono">{data.backup_filename}</span>
                </div>
                <div className="bg-green-50 rounded p-2 md:col-span-2">
                  <span className="text-gray-400">新文件：</span>
                  <span className="font-mono">{data.new_filename}</span>
                </div>
              </div>

              {/* 改写后内容 */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-semibold text-gray-700">
                    修改后预览
                  </h3>
                  <button
                    onClick={handleCopy}
                    className="text-xs text-primary-600 hover:text-primary-700"
                  >
                    {copied ? '✓ 已复制' : '📋 复制全文'}
                  </button>
                </div>
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-800 whitespace-pre-wrap font-sans max-h-[45vh] overflow-y-auto">
                  {data.modified_content}
                </pre>
              </div>
            </>
          )}
        </div>

        {/* 底部操作 */}
        {data && !loading && !error && (
          <div className="flex items-center justify-end gap-2 p-4 border-t bg-gray-50">
            <a
              href={data.new_file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm bg-white hover:bg-gray-50 border border-gray-300 px-4 py-2 rounded-lg"
            >
              👁 在线查看
            </a>
            <a
              href={data.new_file_url}
              download={data.new_filename}
              className="text-sm bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg"
            >
              ⬇️ 下载修改版
            </a>
          </div>
        )}
      </div>
    </div>
  )
}


export default function ScoreResult({ record }) {
  // 修改简历弹窗相关 state
  const [modifyOpen, setModifyOpen] = useState(false)
  const [modifyLoading, setModifyLoading] = useState(false)
  const [modifyData, setModifyData] = useState(null)
  const [modifyError, setModifyError] = useState('')
  const [modifyGlobalError, setModifyGlobalError] = useState('')

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

  const canModify = resume_improvements && resume_improvements.length > 0

  const openModify = async () => {
    if (!canModify) return
    setModifyOpen(true)
    setModifyError('')
    setModifyData(null)
    setModifyLoading(true)
    try {
      const r = await axios.post(`${API}/resumes/modify`, {
        resume_id: record.resume_id,
        improvements: resume_improvements,
        score_record_id: record.id,
      })
      setModifyData(r.data)
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setModifyError(detail)
    } finally {
      setModifyLoading(false)
    }
  }

  const closeModify = () => {
    setModifyOpen(false)
  }

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

      {/* 一键优化简历按钮 */}
      {canModify && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-3 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            <span className="font-medium text-primary-700">💡 根据上面的「简历改进建议」</span>
            ，让 LLM 一键重写简历（原文件自动备份，模板沿用原格式）。
          </div>
          <button
            onClick={openModify}
            disabled={modifyLoading}
            className="text-sm bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white px-4 py-2 rounded-lg shrink-0 ml-3"
          >
            ✨ 一键优化简历
          </button>
        </div>
      )}

      {/* 修改简历全局错误条 */}
      {modifyGlobalError && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded text-xs">
          {modifyGlobalError}
        </div>
      )}

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

      {/* 修改简历弹窗 */}
      <ModifyResumeModal
        open={modifyOpen}
        loading={modifyLoading}
        data={modifyData}
        error={modifyError}
        onClose={closeModify}
        onRetry={openModify}
      />
    </div>
  )
}
