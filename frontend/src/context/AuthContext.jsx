import { createContext, useContext, useState, useEffect } from 'react'
import client from '../api/client'

const AuthContext = createContext({})

export const useAuth = () => useContext(AuthContext)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On app load, restore user from localStorage
  useEffect(() => {
    const restoreAuth = async () => {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const res = await client.get('/api/auth/me')
        const userData = res.data?.data || res.data
        setUser(userData)
      } catch (err) {
        // Token expired or invalid — clear it
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    restoreAuth()
  }, [])

  const login = async (email, password) => {
    const res = await client.post('/api/auth/login', { email, password })
    const data = res.data?.data || res.data

    // Save tokens to localStorage
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))

    setUser(data.user)
    return data
  }

  const register = async (name, email, password, role = 'customer', gender = null, city = null) => {
    const res = await client.post('/api/auth/register', {
      name,
      email,
      password,
      role,
      gender,
      city
    })
    const data = res.data?.data || res.data

    // Save tokens to localStorage
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))

    setUser(data.user)
    return data
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/login'
  }

  const updateUser = (updatedUser) => {
    setUser(updatedUser)
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      loading,
      login,
      register,
      logout,
      updateUser
    }}>
      {children}
    </AuthContext.Provider>
  )
}
