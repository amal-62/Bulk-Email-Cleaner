import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import CategoryBadge from '../components/CategoryBadge'
import api from '../api/client'

interface EmailDetail {
  message_id: string
  subject: string
  summary: string
  category: string
  priority: number
  action_needed: boolean
}

export default function EmailPage() {
  const { id } = useParams()          // Get email ID from URL
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()
  const [detail, setDetail] = useState<EmailDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return

    // Call our AI summarise endpoint with this email's ID
    api.post('/ai/summarise', { message_id: id })
      .then(res => {
        setDetail(res.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [id])

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate('/inbox')}
          className="text-gray-500 hover:text-gray-700 transition-colors"
        >
          ← Back
        </button>
        <h1 className="text-lg font-semibold text-gray-800">Email Summary</h1>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-3">🤖</div>
            <p className="text-gray-500">AI is reading this email...</p>
          </div>
        ) : detail ? (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">

            {/* Subject */}
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {detail.subject}
            </h2>

            {/* Badges */}
            <div className="flex gap-2 flex-wrap mb-6">
              <CategoryBadge category={detail.category} />
              {detail.action_needed && (
                <span className="text-xs font-medium px-2 py-1 rounded-full bg-orange-50 text-orange-600">
                  ⚡ Action needed
                </span>
              )}
              <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                Priority: {detail.priority}/5
              </span>
            </div>

            {/* AI Summary */}
            <div className="bg-blue-50 rounded-xl p-4">
              <p className="text-sm font-semibold text-blue-700 mb-2">
                🤖 AI Summary
              </p>
              <p className="text-gray-700 leading-relaxed">
                {detail.summary}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-400 py-8">Could not load email</p>
        )}
      </div>
    </div>
  )
}