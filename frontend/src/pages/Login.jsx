import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

export default function Login() {
  const { t } = useLanguage()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const data = await login(email, password)
      
      // Check for redirect parameter
      const searchParams = new URLSearchParams(window.location.search)
      const redirectTo = searchParams.get('redirect')
      
      if (redirectTo) {
        navigate(redirectTo)
      } else {
        // Redirect based on role
        const role = data.user?.role
        if (role === 'admin') navigate('/admin')
        else if (role === 'provider') navigate('/dashboard/provider')
        else navigate('/dashboard/customer')
      }
      
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-center mb-2 text-primary-700">
          {t('loginTitle')}
        </h1>
        <p className="text-center text-gray-600 mb-8">आपको खाता वर्तमान राख्नुहोस्</p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-gray-700 font-semibold mb-2">
              {t('email')}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="your@email.com"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 font-semibold mb-2">
              {t('password')}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-700 text-white font-semibold py-3 rounded-lg hover:bg-primary-800 transition-colors disabled:opacity-50"
          >
            {loading ? 'लग इन हो रहेको छ...' : t('login')}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          {t('noAccount')}{' '}
          <Link to="/register" className="text-primary-700 font-semibold hover:underline">
            {t('signUp')}
          </Link>
        </p>

        {/* Demo Credentials */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm font-semibold text-blue-900 mb-2">डेमो खाता:</p>
          <p className="text-xs text-blue-800">ग्राहक: customer1@sewasathi.com / customer123</p>
          <p className="text-xs text-blue-800">प्रदान गर्नेहरू: provider1@sewasathi.com / provider123</p>
        </div>
      </div>
    </div>
  )
}
