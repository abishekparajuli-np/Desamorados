import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'customer',
    gender: '',
    city: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { register } = useAuth()

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const data = await register(
        formData.name,
        formData.email,
        formData.password,
        formData.role,
        formData.gender,
        formData.city
      )
      
      const role = data.user?.role
      if (role === 'admin') navigate('/admin')
      else if (role === 'provider') navigate('/dashboard/provider')
      else navigate('/dashboard/customer')
      
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const nepaliCities = ['काठमाडौ', 'ललितपुर', 'भक्तपुर', 'पोखरा', 'वीरगंज', 'जनकपुर']

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-purple-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-center mb-2 text-primary-700">
          सेवासाथीमा साइन अप गर्नुहोस्
        </h1>
        <p className="text-center text-gray-600 mb-8">आपको खाता सिर्जना गर्नुहोस्</p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-700 font-semibold mb-2">नाम</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="तपाइंको नाम"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 font-semibold mb-2">ईमेल</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="your@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 font-semibold mb-2">पासवर्ड</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="••••••••"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 font-semibold mb-2">भूमिका</label>
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="customer">ग्राहक</option>
              <option value="provider">सेवा प्रदान गर्नेहरू</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-700 font-semibold mb-2">लिङ्ग</label>
            <select
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">चयन गर्नुहोस्</option>
              <option value="male">पुरुष</option>
              <option value="female">महिला</option>
              <option value="other">अन्य</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-700 font-semibold mb-2">शहर</label>
            <select
              name="city"
              value={formData.city}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">चयन गर्नुहोस्</option>
              {nepaliCities.map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-700 text-white font-semibold py-3 rounded-lg hover:bg-primary-800 transition-colors disabled:opacity-50 mt-6"
          >
            {loading ? 'साइन अप हो रहेको छ...' : 'साइन अप गर्नुहोस्'}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          पहिले सदस्य?{' '}
          <Link to="/login" className="text-primary-700 font-semibold hover:underline">
            लग इन गर्नुहोस्
          </Link>
        </p>
      </div>
    </div>
  )
}
