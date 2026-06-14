import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState('Checking...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.message))
      .catch(() => setStatus('Could not reach backend'))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow p-8 text-center">
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">
          Smart Email Assistant
        </h1>
        <p className="text-gray-500">
          Backend says:{' '}
          <span className="text-green-600 font-medium">{status}</span>
        </p>
      </div>
    </div>
  )
}

export default App