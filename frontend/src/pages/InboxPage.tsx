import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Navigate } from 'react-router-dom'
import EmailCard from '../components/EmailCard'
import api from '../api/client'

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

export default function InboxPage() {
  const { isLoggedIn, logout } = useAuth()
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('All')

  // If not logged in, redirect to login page
  if (!isLoggedIn) return <Navigate to="/" />

  const categories = ['All', 'Urgent', 'Newsletter', 'Receipt', 'Social', 'Spam', 'Other']

  useEffect(() => {
    // Fetch and categorise emails when the page loads
    api.get('/ai/categorise-inbox')
      .then(res => {
        setEmails(res.data.emails)
        setLoading(false)
      })
      .catch(err => {
        setError('Failed to load emails')
        setLoading(false)
      })
  }, [])

  // Filter emails by selected category
  const filteredEmails = filter === 'All'
    ? emails
    : emails.filter(e => e.category === filter)

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">📧 Smart Inbox</h1>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          Sign out
        </button>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* Category filter tabs */}
        <div className="flex gap-2 flex-wrap mb-6">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filter === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-300'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-12">
            <div className="text-4xl mb-3">⏳</div>
            <p className="text-gray-500">Loading and categorising your emails...</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="bg-red-50 text-red-600 rounded-xl p-4 text-center">
            {error}
          </div>
        )}

        {/* Email list */}
        {!loading && !error && (
          <div className="flex flex-col gap-3">
            {filteredEmails.length === 0 ? (
              <p className="text-center text-gray-400 py-8">No emails in this category</p>
            ) : (
              filteredEmails.map(email => (
                <EmailCard key={email.id} email={email} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}