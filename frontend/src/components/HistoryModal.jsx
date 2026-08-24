/**
 * 历史记录弹窗 - 命名格式：人名_公司_岗位
 */
export default function HistoryModal({ open, records, onClose, onPick, onDelete }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">📚 历史打分记录</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {records.length === 0 ? (
            <div className="text-center text-gray-400 py-10">还没有记录</div>
          ) : (
            records.map((r) => {
              const color =
                r.overall_score >= 75 ? 'text-green-600' :
                r.overall_score >= 60 ? 'text-yellow-600' : 'text-red-600'
              // 优先用 record_name（人名_公司_岗位）；缺失则回退
              const displayName =
                r.record_name ||
                [r.candidate_name, r.company, r.position].filter(Boolean).join('_') ||
                r.resume_filename
              return (
                <div
                  key={r.id}
                  className="border rounded-lg p-3 hover:border-primary-400 cursor-pointer group"
                  onClick={() => {
                    onPick(r)
                    onClose()
                  }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm text-gray-800 truncate">
                        {displayName}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                        {r.job_description}
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        简历：{r.resume_filename}
                      </div>
                    </div>
                    <div className="text-right shrink-0 flex flex-col items-end gap-1">
                      <div className={`text-2xl font-bold ${color}`}>
                        {r.overall_score}
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(r.created_at).toLocaleString('zh-CN', {
                          month: '2-digit', day: '2-digit',
                          hour: '2-digit', minute: '2-digit',
                        })}
                      </div>
                      {onDelete && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            if (confirm(`删除 "${displayName}" 这条记录？`)) {
                              onDelete(r.id)
                            }
                          }}
                          className="text-xs text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100"
                        >
                          删除
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
