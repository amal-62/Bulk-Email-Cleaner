interface SenderGroup {
  sender_email: string
  sender_name: string | null
  email_count: number
  can_unsubscribe: boolean
  latest_received_at: string | null
}

interface Props {
  sender: SenderGroup
  selected: boolean
  onToggle: () => void
  colorClass: string
  rotation: string
}

function getInitials(name: string | null, email: string) {
  const source = name?.trim() || email
  const parts = source.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return source.slice(0, 2).toUpperCase()
}

export default function SenderRow({ sender, selected, onToggle, colorClass, rotation }: Props) {
  const displayName = sender.sender_name?.trim() || sender.sender_email

  return (
    <label
      className={`flex items-center gap-3.5 px-4 py-3 border-[2.5px] rounded-2xl cursor-pointer transition-colors ${
        selected ? 'border-coral bg-petal' : 'border-ink bg-white hover:bg-mist/40'
      }`}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        aria-label={`Select ${displayName}`}
        className="w-5 h-5 shrink-0"
      />

      <div
        className={`w-[42px] h-[42px] rounded-full border-[2.5px] border-ink flex items-center justify-center font-display font-semibold text-sm shrink-0 ${colorClass}`}
        style={{ transform: rotation }}
      >
        {getInitials(sender.sender_name, sender.sender_email)}
      </div>

      <div className="flex-1 min-w-0">
        <p className="font-bold text-[15px] truncate">{displayName}</p>
        <p className="text-xs text-muted truncate">{sender.sender_email}</p>
      </div>

      {sender.can_unsubscribe ? (
        <span className="pill bg-aqua shrink-0 hidden sm:inline-flex">easy unsubscribe</span>
      ) : (
        <span className="text-xs text-muted font-semibold shrink-0 hidden sm:inline">no unsubscribe link</span>
      )}

      <span className="font-display font-semibold text-lg min-w-[34px] text-right shrink-0">
        {sender.email_count}
      </span>
    </label>
  )
}
