import type { CSSProperties } from 'react'

interface Props {
  size?: number
  fill?: string
  outline?: boolean
  className?: string
  style?: CSSProperties
}

export default function Heart({ size = 24, fill = '#B1E5E6', outline = false, className, style }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" className={className} style={style}>
      <path
        d="M12 21s-8-5.5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.5-8 11-8 11z"
        fill={fill}
        stroke={outline ? '#1f1f1f' : undefined}
        strokeWidth={outline ? 2 : undefined}
      />
    </svg>
  )
}
