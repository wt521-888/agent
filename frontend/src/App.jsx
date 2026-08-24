import { useState, useEffect } from 'react'
import axios from 'axios'
import ResumeManager from './components/ResumeManager'
import JobInput from './components/JobInput'
import ScoreResult from './components/ScoreResult'
import HistoryModal from './components/HistoryModal'

const API = '/api'

export default function App() {
  const [resumes, setResumes] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [currentResult, setCurrentResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [globalError, setGlobalError] = useState('')

  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState([])

  // 加载简历列表
  const loadResumes = async () => {
    try {
      const r = await axios.get(`${API}/resumes`)
      setResumes(r.data)
      // 如果当前选中的被删了，清空
      if (selectedId && !r.data.find((x) => x.id === selectedId)) {
        setSelectedId(null)
        setCurrentResult(null)
      }
    } catch (e) {
      console.error('loadResumes', e)
    }
  }

  const loadHistory = async () => {
    try {
      const r = await axios.get(`${API}/score/history`)
      setHistory(r.data)
    } catch (e) {
      console.error('loadHistory', e)
    }
  }

  useEffect(() => {
    loadResumes()
  }, [])

  // 发起打分
  const handleScore = async (jobDescription) => {
    if (!selectedId) return
    setLoading(true)
    setGlobalError('')
    setCurrentResult(null)
    try {
      const r = await axios.post(`${API}/score`, {
        resume_id: selectedId,
        job_description: jobDescription,
      })
      setCurrentResult(r.data)
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setGlobalError(`打分失败：${detail}`)
    } finally {
      setLoading(false)
    }
  }

  const openHistory = async () => {
    await loadHistory()
    setHistoryOpen(true)
  }

  const handleDeleteRecord = async (id) => {
    try {
      await axios.delete(`${API}/score/history/${id}`)
      setHistory((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setGlobalError(`删除失败：${detail}`)
    }
  }

  return (
    <div className="min-h-screen p-4 md:p-6 max-w-7xl mx-auto">
      {/* 顶部标题栏 */}
      <header className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            🎯 简历智能打分 Agent
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            上传简历 + 招聘信息 → 多维度 LLM 打分 + 学习建议
          </p>
        </div>
        <button
          onClick={openHistory}
          className="text-sm bg-white hover:bg-gray-50 border border-gray-200 px-4 py-2 rounded-lg shadow-sm"
        >
          📚 历史记录
        </button>
      </header>

      {/* 错误条 */}
      {globalError && (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
          {globalError}
        </div>
      )}

      {/* 主体两列布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* 左侧：简历管理 */}
        <aside className="lg:col-span-4">
          <ResumeManager
            resumes={resumes}
            selectedId={selectedId}
            onSelect={(id) => {
              setSelectedId(id)
              setCurrentResult(null)
            }}
            onChange={loadResumes}
          />
        </aside>

        {/* 右侧：JD 输入 + 结果展示 */}
        <main className="lg:col-span-8 space-y-4">
          <JobInput
            disabled={!selectedId}
            loading={loading}
            onSubmit={handleScore}
          />
          {loading ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center text-gray-500">
              <div className="inline-block animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full mb-3" />
              <div>正在调用 Tavily 搜索 + LLM 打分，请稍候…</div>
            </div>
          ) : (
            <ScoreResult record={currentResult} />
          )}
        </main>
      </div>

      <HistoryModal
        open={historyOpen}
        records={history}
        onClose={() => setHistoryOpen(false)}
        onPick={(r) => setCurrentResult(r)}
        onDelete={handleDeleteRecord}
      />
    </div>
  )
}
