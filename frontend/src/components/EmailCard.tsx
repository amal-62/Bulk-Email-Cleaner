import { useNavigate } from 'react-router-dom'
import CategoryBadge from './CategoryBadge'

interface Email {
  id: string
  subject: string
  from: string
  date: string
  snippet: string
  category: string
  priority: number
  action_needed: boolean
  summary: string
}

interface Props {
  email: Email
}

export default function EmailCard({ email }: Props) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/email/${email.id}`)}
      className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-200 cursor-pointer transition-all duration-200"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">

          {/* Sender and date */}
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-medium text-gray-600 truncate">
              {email.from.replace(/<.*>/, '').trim() || email.from}
            </p>
            <p className="text-xs text-gray-400 shrink-0 ml-2">
              {new Date(email.date).toLocaleDateString()}
            </p>
          </div>

          {/* Subject */}
          <h3 className="font-semibold text-gray-800 truncate mb-1">
            {email.subject}
          </h3>

          {/* AI Summary (if available) */}
          {email.summary && (
            <p className="text-sm text-gray-500 line-clamp-2 mb-2">
              {email.summary}
            </p>
          )}

          {/* Badges row */}
          <div className="flex items-center gap-2 flex-wrap">
            <CategoryBadge category={email.category} />

            {/* Priority indicator */}
            {email.priority >= 4 && (
              <span className="text-xs font-medium px-2 py-1 rounded-full bg-red-50 text-red-600">
                🔥 High priority
              </span>
            )}

            {/* Action needed indicator */}
            {email.action_needed && (
              <span className="text-xs font-medium px-2 py-1 rounded-full bg-orange-50 text-orange-600">
                ⚡ Action needed
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}