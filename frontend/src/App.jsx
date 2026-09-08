import { useState, useEffect } from 'react'
import axios from 'axios'
import ResumeManager from './components/ResumeManager'
import JobInput from './components/JobInput'
import ScoreResult from './components/ScoreResult'
import HistoryModal from './components/HistoryModal'
import InterviewModal from './components/InterviewModal'
import ConfigModal from './components/ConfigModal'

const API = '/api'

const apiClient = axios.create({
  timeout: 180000,
})

export default function App() {
  const [resumes, setResumes] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [currentResult, setCurrentResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [globalError, setGlobalError] = useState('')

  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState([])
  
  const [interviewOpen, setInterviewOpen] = useState(false)
  const [interviewData, setInterviewData] = useState({ resumeId: null, jobDescription: '' })
  const [configOpen, setConfigOpen] = useState(false)

  const loadResumes = async () => {
    try {
      const r = await apiClient.get(API + '/resumes')
      setResumes(r.data)
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
      const r = await apiClient.get(API + '/score/history')
      setHistory(r.data)
    } catch (e) {
      console.error('loadHistory', e)
    }
  }

  useEffect(() => {
    loadResumes()
  }, [])

  const handleScore = async (jd) => {
    if (!selectedId) return
    setLoading(true)
    setGlobalError('')
    setCurrentResult(null)
    try {
      const r = await apiClient.post(API + '/score', {
        resume_id: selectedId,
        job_description: jd,
      })
      setCurrentResult(r.data)
    } catch (err) {
      let detail = '未知错误'
      if (err.code === 'ECONNABORTED') {
        detail = '请求超时，请稍后重试'
      } else if (err.response?.data?.detail) {
        detail = err.response.data.detail
      } else if (err.message) {
        detail = err.message
      }
      setGlobalError('打分失败：' + detail)
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
      await apiClient.delete(API + '/score/history/' + id)
      setHistory((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      setGlobalError('删除失败：' + (err.response?.data?.detail || err.message))
    }
  }

  // 打开面试模块（支持从简历或历史记录进入）
  const openInterview = (resumeId, jobDesc) => {
    setInterviewData({ resumeId, jobDescription: jobDesc || '' })
    setInterviewOpen(true)
  }

  return (
    <div className="min-h-screen p-4 md:p-6 max-w-7xl mx-auto">
      {/* 顶部标题栏 */}
      <header className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🎯 简历智能打分 Agent</h1>
          <p className="text-sm text-gray-500 mt-1">上传简历 + 招聘信息 → 多维度 LLM 打分 + 学习建议 + 模拟面试</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => openInterview(selectedId, currentResult?.job_description || '')}
            disabled={!selectedId}
            className="text-sm bg-green-50 hover:bg-green-100 disabled:bg-gray-100 disabled:text-gray-400 text-green-700 border border-green-200 px-4 py-2 rounded-lg"
          >
            🎤 模拟面试
          </button>
          <button onClick={openHistory} className="text-sm bg-white hover:bg-gray-50 border border-gray-200 px-4 py-2 rounded-lg">
            📚 历史记录
          </button>
          <button onClick={() => setConfigOpen(true)} className="text-sm bg-white hover:bg-gray-50 border border-gray-200 px-4 py-2 rounded-lg">
            ⚙️ 配置
          </button>
        </div>
      </header>

      {/* 错误条 */}
      {globalError && (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
          {globalError}
          <button onClick={() => setGlobalError('')} className="ml-2 text-red-500 hover:text-red-700">✕</button>
        </div>
      )}

      {/* 主体两列布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <aside className="lg:col-span-4">
          <ResumeManager resumes={resumes} selectedId={selectedId} onSelect={(id) => { setSelectedId(id); setCurrentResult(null) }} onChange={loadResumes} />
        </aside>

        <main className="lg:col-span-8 space-y-4">
          <JobInput disabled={!selectedId} loading={loading} onSubmit={handleScore} />
          {loading ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center text-gray-500">
              <div className="inline-block animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mb-3" />
              <div>正在调用 LLM 打分，请稍候…</div>
              <div className="text-xs text-gray-400 mt-2">通常需要 30-60 秒</div>
            </div>
          ) : (
            <ScoreResult record={currentResult} onStartInterview={(jd) => openInterview(selectedId, jd)} />
          )}
        </main>
      </div>

      {/* 弹窗 */}
      <HistoryModal
        open={historyOpen}
        records={history}
        onClose={() => setHistoryOpen(false)}
        onPick={(r) => setCurrentResult(r)}
        onDelete={handleDeleteRecord}
        onStartInterview={(r) => openInterview(r.resume_id, r.job_description)}
      />
      
      <InterviewModal
        open={interviewOpen}
        onClose={() => setInterviewOpen(false)}
        resumeId={interviewData.resumeId}
        jobDescription={interviewData.jobDescription}
      />
      
      <ConfigModal open={configOpen} onClose={() => setConfigOpen(false)} />
    </div>
  )
}
