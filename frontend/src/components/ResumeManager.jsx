import { useState, useRef } from 'react'
import axios from 'axios'

const API = '/api'

/**
 * 简历管理组件：上传 / 列表 / 选择 / 删除
 */
export default function ResumeManager({ resumes, selectedId, onSelect, onChange }) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      await axios.post(`${API}/resumes/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onChange()
    } catch (err) {
      setError(err.response?.data?.detail || '上传失败')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除这份简历？相关打分记录也会被删除。')) return
    try {
      await axios.delete(`${API}/resumes/${id}`)
      onChange()
    } catch (err) {
      alert(err.response?.data?.detail || '删除失败')
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">📄 简历管理</h2>
        <label className="cursor-pointer bg-primary-600 hover:bg-primary-700 text-white text-sm px-3 py-1.5 rounded-lg transition">
          {uploading ? '上传中…' : '+ 上传简历'}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.pptx,.xlsx,.html,.md,.csv,.png,.jpg"
            className="hidden"
            disabled={uploading}
            onChange={handleUpload}
          />
        </label>
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded mb-3">
          {error}
        </div>
      )}

      <div className="text-xs text-gray-500 mb-2">
        支持 PDF / DOCX / TXT / PPTX / XLSX / HTML / MD / CSV / 图片，单个文件 ≤ 10MB
      </div>

      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {resumes.length === 0 ? (
          <div className="text-center text-gray-400 py-10 text-sm">
            还没有简历，点击右上角上传
          </div>
        ) : (
          resumes.map((r) => (
            <div
              key={r.id}
              className={`border rounded-lg p-3 cursor-pointer transition ${
                selectedId === r.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
              onClick={() => onSelect(r.id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-800 truncate">
                    {r.filename}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {r.file_type.toUpperCase()} · {formatSize(r.size)} ·{' '}
                    {new Date(r.created_at).toLocaleString('zh-CN')}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(r.id)
                  }}
                  className="text-xs text-red-500 hover:text-red-700 px-2 py-1"
                >
                  删除
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
