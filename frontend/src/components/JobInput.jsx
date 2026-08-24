import { useState } from 'react'

/**
 * 招聘信息输入区 + 打分按钮
 */
export default function JobInput({ disabled, loading, onSubmit }) {
  const [jobDescription, setJobDescription] = useState('')

  const handleClick = () => {
    if (disabled) return
    if (!jobDescription.trim() || jobDescription.trim().length < 10) {
      alert('请输入至少 10 个字的招聘信息')
      return
    }
    onSubmit(jobDescription)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <h2 className="text-lg font-semibold text-gray-800 mb-3">💼 招聘信息</h2>
      <textarea
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        rows={8}
        placeholder="将招聘信息粘贴到这里…&#10;例如：&#10;字节跳动 算法工程师&#10;职责：推荐系统建模…&#10;要求：Python、PyTorch、3 年以上经验…"
        className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
      />
      <div className="flex items-center justify-between mt-3">
        <div className="text-xs text-gray-500">
          {disabled
            ? '⚠️ 请先在左侧选择一份简历'
            : `已输入 ${jobDescription.length} 字`}
        </div>
        <button
          onClick={handleClick}
          disabled={disabled || loading}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition ${
            disabled || loading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 text-white'
          }`}
        >
          {loading ? '打分中…（可能需要 10-30 秒）' : '🚀 开始打分'}
        </button>
      </div>
    </div>
  )
}
