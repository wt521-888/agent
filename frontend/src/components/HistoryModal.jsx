import axios from 'axios'

export default function HistoryModal({ open, records, onClose, onPick, onDelete, onStartInterview }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">📚 历史打分记录</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl">×</button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {records.length === 0 ? (
            <div className="text-center text-gray-500 py-8">暂无记录</div>
          ) : (
            <div className="space-y-3">
              {records.map((r) => (
                <div key={r.id} className="border rounded-lg p-3 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-blue-600">{r.overall_score}</span>
                        <div>
                          <div className="font-medium text-sm">{r.resume_filename}</div>
                          <div className="text-xs text-gray-500">{r.candidate_name} · {r.company} · {r.position}</div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">{new Date(r.created_at).toLocaleString('zh-CN')}</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => { onStartInterview(r); onClose(); }}
                        className="text-xs text-green-600 hover:text-green-700 px-2 py-1 rounded hover:bg-green-50"
                      >
                        🎤 面试
                      </button>
                      <button
                        onClick={() => { onPick(r); onClose(); }}
                        className="text-xs text-blue-600 hover:text-blue-700 px-2 py-1 rounded hover:bg-blue-50"
                      >
                        查看
                      </button>
                      <button
                        onClick={() => onDelete(r.id)}
                        className="text-xs text-red-600 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
