import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

// Define the shape of our auth context
// This is what any component can access when they use useAuth()
interface AuthContextType {
  token: string | null        // The JWT token
  isLoggedIn: boolean         // Whether the user is logged in
  login: (token: string) => void   // Function to log in
  logout: () => void          // Function to log out
}

// Create the context with a default value of null
const AuthContext = createContext<AuthContextType | null>(null)

// This component wraps your entire app and provides auth state to all children
export function AuthProvider({ children }: { children: ReactNode }) {
  // Read token from localStorage on first load
  // This means the user stays logged in even after refreshing the page
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('token')
  )

  const isLoggedIn = !!token  // Convert token to boolean (null = false, string = true)

  function login(newToken: string) {
    localStorage.setItem('token', newToken)  // Save to localStorage for persistence
    setToken(newToken)                        // Update state to trigger re-render
  }

  function logout() {
    localStorage.removeItem('token')  // Remove from localStorage
    setToken(null)                    // Clear state
  }

  // On first load, check if there's a token in the URL
  // This is how we receive the JWT after Google OAuth redirect
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      login(urlToken)
      // Clean the token from the URL so it's not visible
      window.history.replaceState({}, '', '/')
    }
  }, [])

  return (
    <AuthContext.Provider value={{ token, isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook — any component can call useAuth() to get auth state
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}