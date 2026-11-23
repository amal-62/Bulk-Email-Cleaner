import type { ReactNode } from 'react'
import Bunny from './Bunny'

interface Props {
  title: string
  left?: ReactNode
  right?: ReactNode
}

export default function PageHeader({ title, left, right }: Props) {
  return (
    <header className="relative bg-white border-b-[2.5px] border-ink px-4 sm:px-8 py-3 flex items-center gap-3">
      {left}
      <div className="h-[50px] w-[44px] overflow-hidden shrink-0">
        <Bunny size={44} />
      </div>
      <h1 className="text-2xl font-bold flex-1">{title}</h1>
      {right}
    </header>
  )
}
