import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Navigate } from 'react-router-dom'
import SenderRow from '../components/SenderRow'
import PageHeader from '../components/PageHeader'
import api from '../api/client'

interface SenderGroup {
  sender_email: string
  sender_name: string | null
  email_count: number
  can_unsubscribe: boolean
  latest_received_at: string | null
}

interface Notice {
  kind: 'ok' | 'error'
  text: string
}

const AVATAR_COLORS = ['bg-blush', 'bg-aqua', 'bg-mist', 'bg-coral']
const ROTATIONS = ['rotate(-2deg)', 'rotate(1deg)', 'rotate(-1deg)', 'rotate(2deg)']

export default function InboxPage() {
  const { isLoggedIn, logout } = useAuth()
  const [senders, setSenders] = useState<SenderGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [notice, setNotice] = useState<Notice | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [trashing, setTrashing] = useState(false)
  const [unsubscribing, setUnsubscribing] = useState(false)
  const [syncing, setSyncing] = useState(false)


  useEffect(() => {
    api.get('/emails/grouped')
      .then(res => {
        setSenders(res.data.senders)
        setLoading(false)
      })
      .catch(() => {
        setLoadError('Failed to load emails')
        setLoading(false)
      })
  }, [])

  if (!isLoggedIn) return <Navigate to="/" />

  function toggleSender(email: string) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(email)) next.delete(email)
      else next.add(email)
      return next
    })
  }

  function toggleSelectAll() {
    if (selected.size === senders.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(senders.map(s => s.sender_email)))
    }
  }

  async function handleSync() {
    setSyncing(true)
    setNotice(null)
    try {
      const res = await api.post('/emails/sync')
      const refreshed = await api.get('/emails/grouped')
      setSenders(refreshed.data.senders)
      setLoadError('')
      setSelected(new Set())
      setNotice({ kind: 'ok', text: `Synced ${res.data.synced} emails.` })
    } catch {
      setNotice({ kind: 'error', text: 'Sync failed — try signing out and back in.' })
    } finally {
      setSyncing(false)
    }
  }

  async function handleUnsubscribeSelected() {
    if (selected.size === 0) return
    const senderEmails = Array.from(selected)
    const noLink = senders.filter(s => selected.has(s.sender_email) && !s.can_unsubscribe).length
    setUnsubscribing(true)
    setNotice(null)
    try {
      const res = await api.post('/emails/unsubscribe', { sender_emails: senderEmails })
      const { unsubscribed, failed } = res.data
      const skipped = noLink > 0 ? ` ${noLink} had no unsubscribe link.` : ''

      if (unsubscribed === 0 && failed > 0) {
        setNotice({ kind: 'error', text: `Couldn't unsubscribe from any of the ${failed} selected sender(s).${skipped}` })
      } else if (failed > 0) {
        setNotice({ kind: 'error', text: `Unsubscribed from ${unsubscribed}, but ${failed} failed.${skipped}` })
      } else if (unsubscribed === 0) {
        setNotice({ kind: 'error', text: 'None of the selected senders have an unsubscribe link.' })
      } else {
        setNotice({ kind: 'ok', text: `Unsubscribed from ${unsubscribed} sender(s).${skipped}` })
      }
      setSelected(new Set())
    } catch {
      setNotice({ kind: 'error', text: 'Failed to unsubscribe from selected senders' })
    } finally {
      setUnsubscribing(false)
    }
  }

  async function handleTrashSelected() {
    if (selected.size === 0) return
    const senderEmails = Array.from(selected)
    setTrashing(true)
    setNotice(null)
    try {
      const res = await api.post('/emails/trash', { sender_emails: senderEmails })
      const { trashed, failed } = res.data

      if (failed > 0 && trashed === 0) {
        setNotice({
          kind: 'error',
          text:
            `Gmail rejected the trash request for all ${failed} email(s). ` +
            `This usually means the app doesn't have permission to modify your inbox yet — ` +
            `check the Gmail API scope and re-login.`,
        })
      } else if (failed > 0) {
        setNotice({ kind: 'error', text: `${trashed} trashed, but ${failed} failed — refreshing to show the real state.` })
      } else {
        setNotice({ kind: 'ok', text: `Cleared out ${trashed} email(s).` })
      }

      
      const refreshed = await api.get('/emails/grouped')
      setSenders(refreshed.data.senders)
      setSelected(new Set())
    } catch {
      setNotice({ kind: 'error', text: 'Failed to trash selected emails' })
    } finally {
      setTrashing(false)
    }
  }

  const totalEmails = senders.reduce((sum, s) => sum + s.email_count, 0)

  return (
    <div className="grid-paper min-h-screen">
      <PageHeader
        title="Inbox"
        right={
          <>
            <button onClick={handleSync} disabled={syncing} className="btn bg-mist">
              {syncing ? 'Syncing...' : 'Sync inbox'}
            </button>
            <button onClick={logout} className="btn">
              Sign out
            </button>
          </>
        }
      />

      <div className="max-w-2xl mx-auto px-4 py-7">
        {!loading && !loadError && (
          <p className="mb-4">
            <span className="pill bg-mist text-[13px]">
              {totalEmails.toLocaleString()} emails synced &middot; {senders.length} senders
            </span>
          </p>
        )}

        {loading && (
          <div className="sticker text-center py-10">
            <p className="font-display font-semibold">Loading your inbox...</p>
          </div>
        )}

        {loadError && (
          <div role="alert" className="sticker !bg-petal text-center p-4 font-semibold">
            {loadError}
          </div>
        )}

        {!loading && !loadError && (
          <>
            {notice && (
              <div
                role={notice.kind === 'error' ? 'alert' : 'status'}
                className={`rounded-2xl border-[2.5px] border-ink p-3 text-sm font-semibold mb-4 ${
                  notice.kind === 'error' ? 'bg-petal' : 'bg-mist'
                }`}
              >
                {notice.text}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 px-4 py-2.5 bg-mist border-[2.5px] border-ink rounded-2xl shadow-[4px_4px_0_var(--color-blush)] mb-4">
              <input
                type="checkbox"
                aria-label="Select all"
                checked={senders.length > 0 && selected.size === senders.length}
                onChange={toggleSelectAll}
                className="w-5 h-5"
              />
              <span className="text-sm font-bold flex-1">
                {selected.size > 0 ? `${selected.size} selected` : 'Select all'}
              </span>
              <button
                onClick={handleUnsubscribeSelected}
                disabled={selected.size === 0 || unsubscribing}
                className="btn bg-aqua !text-sm"
              >
                {unsubscribing ? 'Unsubscribing...' : 'Unsubscribe me'}
              </button>
              <button
                onClick={handleTrashSelected}
                disabled={selected.size === 0 || trashing}
                className="btn bg-coral !text-sm"
              >
                {trashing ? 'Clearing...' : 'Clear these out'}
              </button>
            </div>

            <div className="flex flex-col gap-2.5">
              {senders.length === 0 ? (
                <p className="sticker text-center text-muted py-8 px-4">
                  No emails synced yet — press “Sync inbox” to see your senders here.
                </p>
              ) : (
                senders.map((sender, i) => (
                  <SenderRow
                    key={sender.sender_email}
                    sender={sender}
                    selected={selected.has(sender.sender_email)}
                    onToggle={() => toggleSender(sender.sender_email)}
                    colorClass={AVATAR_COLORS[i % AVATAR_COLORS.length]}
                    rotation={ROTATIONS[i % ROTATIONS.length]}
                  />
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
