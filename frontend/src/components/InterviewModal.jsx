import { useState, useEffect } from 'react'
import axios from 'axios'

const API = '/api'

export default function InterviewModal({ open, onClose, resumeId, jobDescription }) {
  const [step, setStep] = useState('setup')
  const [numQuestions, setNumQuestions] = useState(5)
  const [questions, setQuestions] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answer, setAnswer] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [localJobDesc, setLocalJobDesc] = useState('')

  // 当弹窗打开时，同步外部传入的 jobDescription
  useEffect(() => {
    if (open) {
      setLocalJobDesc(jobDescription || '')
      setStep('setup')
      setQuestions([])
      setResults([])
      setError('')
    }
  }, [open, jobDescription])

  if (!open) return null

  const currentJobDesc = localJobDesc || jobDescription

  const generateQuestions = async () => {
    if (!currentJobDesc || currentJobDesc.length < 10) {
      setError('请输入岗位描述（至少10字）')
      return
    }
    if (!resumeId) {
      setError('请先选择简历')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await axios.post(API + '/interview/questions', {
        resume_id: resumeId,
        job_description: currentJobDesc,
        num_questions: numQuestions,
      })
      setQuestions(res.data.questions)
      setStep('questions')
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const startInterview = () => {
    setCurrentQuestion(0)
    setResults([])
    setAnswer('')
    setStep('answering')
  }

  const submitAnswer = async () => {
    if (!answer.trim()) return
    setLoading(true)
    setError('')
    try {
      const question = questions[currentQuestion]
      const res = await axios.post(API + '/interview/evaluate', {
        question: question.question,
        answer: answer,
        job_description: currentJobDesc,
        key_points: question.key_points || [],
      })
      const newResults = [...results, { question, answer, evaluation: res.data }]
      setResults(newResults)
      if (currentQuestion < questions.length - 1) {
        setCurrentQuestion(currentQuestion + 1)
        setAnswer('')
      } else {
        setStep('result')
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const averageScore = results.length > 0
    ? Math.round(results.reduce((sum, r) => sum + r.evaluation.overall_score, 0) / results.length)
    : 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">
            🎤 模拟面试
            {step === 'answering' && <span className="text-sm font-normal text-gray-500 ml-2">{currentQuestion + 1} / {questions.length}</span>}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl">×</button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {error && <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}

          {/* 设置阶段 */}
          {step === 'setup' && (
            <div className="text-center py-8">
              <h3 className="text-xl font-semibold mb-4">准备开始模拟面试</h3>
              <p className="text-gray-600 mb-6">AI 将根据简历和岗位生成面试问题</p>
              
              {/* 岗位描述输入 */}
              <div className="max-w-md mx-auto mb-4 text-left">
                <label className="block text-sm font-medium text-gray-700 mb-1">岗位描述</label>
                <textarea
                  value={localJobDesc}
                  onChange={(e) => setLocalJobDesc(e.target.value)}
                  placeholder="请输入目标岗位的职责和要求..."
                  className="w-full h-24 border rounded-lg p-3 resize-none"
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">面试问题数量</label>
                <select value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))} className="border rounded-lg px-4 py-2">
                  {[3, 5, 7, 10].map(n => <option key={n} value={n}>{n} 题</option>)}
                </select>
              </div>
              <button onClick={generateQuestions} disabled={loading} className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-6 py-3 rounded-lg font-medium">
                {loading ? '生成中...' : '开始生成面试题'}
              </button>
            </div>
          )}

          {/* 问题列表 */}
          {step === 'questions' && (
            <div>
              <h3 className="font-semibold mb-4">面试题目预览</h3>
              <div className="space-y-3 mb-6">
                {questions.map((q, i) => (
                  <div key={q.id} className="bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-blue-600">{q.category}</span>
                      <span className="text-xs text-gray-500">{q.difficulty}</span>
                    </div>
                    <p className="text-sm">{q.question}</p>
                  </div>
                ))}
              </div>
              <button onClick={startInterview} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium">开始面试</button>
            </div>
          )}

          {/* 答题阶段 */}
          {step === 'answering' && questions[currentQuestion] && (
            <div>
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-blue-600">{questions[currentQuestion].category}</span>
                  <span className="text-xs text-gray-500">{questions[currentQuestion].difficulty}</span>
                </div>
                <p className="font-medium">{questions[currentQuestion].question}</p>
                {questions[currentQuestion].key_points?.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">考察要点: {questions[currentQuestion].key_points.join(', ')}</div>
                )}
              </div>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="请输入你的回答..."
                className="w-full h-40 border rounded-lg p-3 resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button onClick={submitAnswer} disabled={loading || !answer.trim()} className="mt-3 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-3 rounded-lg font-medium">
                {loading ? '评估中...' : '提交回答'}
              </button>
            </div>
          )}

          {/* 结果展示 */}
          {step === 'result' && (
            <div>
              <div className="text-center mb-6">
                <div className="text-5xl font-bold text-blue-600 mb-2">{averageScore}</div>
                <div className="text-gray-500">综合得分</div>
              </div>
              
              <div className="space-y-4">
                {results.map((r, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">问题 {i + 1}</span>
                      <span className="text-lg font-bold text-blue-600">{r.evaluation.overall_score}</span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{r.question.question}</p>
                    <p className="text-sm bg-gray-50 rounded p-2 mb-2">你的回答: {r.answer}</p>
                    
                    <div className="grid grid-cols-4 gap-2 mb-2">
                      {Object.entries(r.evaluation.scores).map(([key, value]) => (
                        <div key={key} className="text-center">
                          <div className="text-xs text-gray-500">
                            {key === 'accuracy' ? '准确性' : key === 'completeness' ? '完整性' : key === 'depth' ? '深度' : '表达'}
                          </div>
                          <div className="font-semibold">{value}</div>
                        </div>
                      ))}
                    </div>
                    
                    {r.evaluation.strengths?.length > 0 && (
                      <div className="text-xs text-green-600 mb-1">优点: {r.evaluation.strengths.join(', ')}</div>
                    )}
                    {r.evaluation.weaknesses?.length > 0 && (
                      <div className="text-xs text-red-600 mb-1">不足: {r.evaluation.weaknesses.join(', ')}</div>
                    )}
                    {r.evaluation.improvement_suggestions?.length > 0 && (
                      <div className="text-xs text-orange-600 mb-1">建议: {r.evaluation.improvement_suggestions.join(', ')}</div>
                    )}
                    
                    <details className="mt-2">
                      <summary className="text-xs text-blue-600 cursor-pointer">查看参考答案</summary>
                      <p className="text-xs text-gray-600 mt-1">{r.evaluation.reference_answer}</p>
                    </details>
                  </div>
                ))}
              </div>
              
              <div className="flex gap-3 mt-6">
                <button onClick={() => { setStep('setup'); setQuestions([]); setResults([]); }} className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 rounded-lg font-medium">重新开始</button>
                <button onClick={onClose} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium">关闭</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
