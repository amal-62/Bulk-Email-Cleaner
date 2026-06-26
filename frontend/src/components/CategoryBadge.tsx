// Maps each category to a colour scheme
const categoryStyles: Record<string, string> = {
  Urgent:     'bg-red-100 text-red-700',
  Newsletter: 'bg-blue-100 text-blue-700',
  Receipt:    'bg-green-100 text-green-700',
  Social:     'bg-purple-100 text-purple-700',
  Spam:       'bg-gray-100 text-gray-500',
  Other:      'bg-yellow-100 text-yellow-700',
}

interface Props {
  category: string
}

export default function CategoryBadge({ category }: Props) {
  const style = categoryStyles[category] || categoryStyles.Other

  return (
    <span className={`text-xs font-medium px-2 py-1 rounded-full ${style}`}>
      {category}
    </span>
  )
}