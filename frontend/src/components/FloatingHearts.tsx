import Heart from './Heart'

// Decorative hearts floating on the graph paper
export default function FloatingHearts() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <Heart size={56} fill="#B1E5E6" className="absolute left-[8%] top-[22%] -rotate-12" />
      <Heart size={44} fill="#F7ADAD" className="absolute right-[10%] top-[14%] rotate-12" />
      <Heart size={64} fill="#B1E5E6" className="absolute right-[7%] bottom-[22%] rotate-6" />
      <Heart size={40} fill="#F7ADAD" className="absolute left-[6%] bottom-[18%] -rotate-6" />
    </div>
  )
}
