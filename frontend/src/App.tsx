import { Routes, Route } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import InboxPage from './pages/InboxPage'
import EmailPage from './pages/EmailPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/inbox" element={<InboxPage />} />
      <Route path="/email/:id" element={<EmailPage />} />
    </Routes>
  )
}