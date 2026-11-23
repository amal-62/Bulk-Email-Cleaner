import { Routes, Route } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import InboxPage from './pages/InboxPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/inbox" element={<InboxPage />} />
    </Routes>
  )
}