import { useState, useEffect } from 'react'
import axios from 'axios'

const API = '/api'

export default function ConfigModal({ open, onClose }) {
  const [config, setConfig] = useState({
    openai_api_key: '',
    openai_base_url: '',
    openai_model: '',
    vision_model: '',
    tavily_api_key: '',
  })
  const [editMode, setEditMode] = useState(false)
  const [formData, setFormData] = useState({})
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (open) {
      loadConfig()
      setEditMode(false)
      setError('')
      setSuccess('')
    }
  }, [open])

  const loadConfig = async () => {
    try {
      const res = await axios.get(API + '/config')
      setConfig(res.data)
      setFormData(res.data)
    } catch (err) {
      setError('加载配置失败')
    }
  }

  const handleSave = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const updates = {}
      if (formData.openai_api_key && !formData.openai_api_key.includes('****')) {
        updates.openai_api_key = formData.openai_api_key
      }
      if (formData.openai_base_url !== config.openai_base_url) {
        updates.openai_base_url = formData.openai_base_url
      }
      if (formData.openai_model !== config.openai_model) {
        updates.openai_model = formData.openai_model
      }
      if (formData.vision_model !== config.vision_model) {
        updates.vision_model = formData.vision_model
      }
      if (formData.tavily_api_key && !formData.tavily_api_key.includes('****')) {
        updates.tavily_api_key = formData.tavily_api_key
      }

      if (Object.keys(updates).length === 0) {
        setEditMode(false)
        return
      }

      await axios.put(API + '/config', updates)
      setSuccess('配置保存成功')
      await loadConfig()
      setEditMode(false)
    } catch (err) {
      setError(err.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await axios.post(API + '/config/test-openai')
      setTestResult(res.data)
    } catch (err) {
      setTestResult({ success: false, error: err.message })
    } finally {
      setTesting(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">⚙️ API 配置</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl">×</button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {error && <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}
          {success && <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{success}</div>}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              {editMode ? (
                <input type="password" value={formData.openai_api_key} onChange={(e) => setFormData({...formData, openai_api_key: e.target.value})} placeholder="输入新的 API Key" className="w-full border rounded-lg px-3 py-2" />
              ) : (
                <div className="text-gray-600 bg-gray-50 rounded-lg px-3 py-2">{config.openai_api_key}</div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
              {editMode ? (
                <input type="text" value={formData.openai_base_url} onChange={(e) => setFormData({...formData, openai_base_url: e.target.value})} placeholder="https://api.openai.com/v1" className="w-full border rounded-lg px-3 py-2" />
              ) : (
                <div className="text-gray-600 bg-gray-50 rounded-lg px-3 py-2">{config.openai_base_url}</div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">主模型</label>
              {editMode ? (
                <input type="text" value={formData.openai_model} onChange={(e) => setFormData({...formData, openai_model: e.target.value})} placeholder="gpt-4o-mini" className="w-full border rounded-lg px-3 py-2" />
              ) : (
                <div className="text-gray-600 bg-gray-50 rounded-lg px-3 py-2">{config.openai_model}</div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">视觉模型（OCR 用）</label>
              {editMode ? (
                <input type="text" value={formData.vision_model} onChange={(e) => setFormData({...formData, vision_model: e.target.value})} placeholder="gpt-4o" className="w-full border rounded-lg px-3 py-2" />
              ) : (
                <div className="text-gray-600 bg-gray-50 rounded-lg px-3 py-2">{config.vision_model}</div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tavily API Key</label>
              {editMode ? (
                <input type="password" value={formData.tavily_api_key} onChange={(e) => setFormData({...formData, tavily_api_key: e.target.value})} placeholder="tvly-..." className="w-full border rounded-lg px-3 py-2" />
              ) : (
                <div className="text-gray-600 bg-gray-50 rounded-lg px-3 py-2">{config.tavily_api_key}</div>
              )}
            </div>
          </div>

          {editMode && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <button onClick={testConnection} disabled={testing} className="text-sm text-blue-600 hover:text-blue-700">
                {testing ? '测试中...' : '🔗 测试 API 连接（验证 Key 是否可用）'}
              </button>
              {testResult && (
                <div className={'mt-2 text-sm ' + (testResult.success ? 'text-green-600' : 'text-red-600')}>
                  {testResult.success ? '✓ 连接成功！模型响应正常' : '✗ 连接失败: ' + (testResult.error || '')}
                </div>
              )}
            </div>
          )}

          {editMode && (
            <div className="mt-4">
              <div className="text-sm font-medium text-gray-700 mb-2">常用配置（点击快速填入）:</div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setFormData({...formData, openai_base_url: 'https://api.openai.com/v1', openai_model: 'gpt-4o-mini', vision_model: 'gpt-4o'})} className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">OpenAI</button>
                <button onClick={() => setFormData({...formData, openai_base_url: 'https://api.xiaomimimo.com/v1', openai_model: 'mimo-v2.5-pro', vision_model: 'mimo-v2.5'})} className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">小米 MiMo</button>
                <button onClick={() => setFormData({...formData, openai_base_url: 'https://api.deepseek.com/v1', openai_model: 'deepseek-chat', vision_model: 'deepseek-chat'})} className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">DeepSeek</button>
                <button onClick={() => setFormData({...formData, openai_base_url: 'https://api.moonshot.cn/v1', openai_model: 'moonshot-v1-8k', vision_model: 'moonshot-v1-8k'})} className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">Moonshot</button>
                <button onClick={() => setFormData({...formData, openai_base_url: 'https://open.bigmodel.cn/api/paas/v4', openai_model: 'glm-4-flash', vision_model: 'glm-4v'})} className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">智谱</button>
                <button onClick={() => setFormData({...formData, openai_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', openai_model: 'qwen-turbo', vision_model: 'qwen-vl-plus'})} className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">通义千问</button>
              </div>
            </div>
          )}
        </div>

        <div className="border-t p-4 flex justify-end gap-3">
          {editMode ? (
            <>
              <button onClick={() => { setEditMode(false); setFormData(config); }} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">取消</button>
              <button onClick={handleSave} disabled={loading} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg">
                {loading ? '保存中...' : '保存'}
              </button>
            </>
          ) : (
            <button onClick={() => setEditMode(true)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">编辑配置</button>
          )}
        </div>
      </div>
    </div>
  )
}
