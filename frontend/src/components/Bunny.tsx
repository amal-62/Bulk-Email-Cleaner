interface Props {
  size?: number
  label?: string // omit for purely decorative use
}

// Miffy-inspired bunny mascot, drawn as inline SVG so it needs no image files.
export default function Bunny({ size = 120, label }: Props) {
  const ink = '#1f1f1f'
  return (
    <svg
      width={size}
      viewBox="0 0 200 240"
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      className="block shrink-0"
    >
      <g stroke={ink} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
        <path d="M72 74C56 42 60 6 78 6S98 42 92 74Z" fill="#fff" />
        <path d="M128 74C144 42 140 6 122 6S102 42 108 74Z" fill="#fff" />
        <path d="M60 160Q100 150 140 160L150 208Q100 228 50 208Z" fill="#B1E5E6" />
        <ellipse cx="44" cy="170" rx="16" ry="20" transform="rotate(25 44 170)" fill="#fff" />
        <ellipse cx="156" cy="170" rx="16" ry="20" transform="rotate(-25 156 170)" fill="#fff" />
        <ellipse cx="76" cy="222" rx="21" ry="15" fill="#fff" />
        <ellipse cx="124" cy="222" rx="21" ry="15" fill="#fff" />
        <ellipse cx="100" cy="112" rx="54" ry="48" fill="#fff" />
        <path d="M78 156Q100 176 122 156Z" fill="#CCFBFA" />
        <path d="M95 123l10 9M105 123l-10 9" fill="none" strokeWidth="3" />
      </g>
      <ellipse cx="82" cy="110" rx="4" ry="6" fill={ink} />
      <ellipse cx="118" cy="110" rx="4" ry="6" fill={ink} />
      <ellipse cx="68" cy="124" rx="8" ry="5" fill="#F7ADAD" />
      <ellipse cx="132" cy="124" rx="8" ry="5" fill="#F7ADAD" />
      <circle cx="100" cy="184" r="4" fill="#F7ADAD" />
      <circle cx="100" cy="200" r="4" fill="#F7ADAD" />
    </svg>
  )
}
