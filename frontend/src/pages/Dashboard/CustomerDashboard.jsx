import React, { useState, useEffect } from 'react'
import { Calendar, MapPin, DollarSign, Star, Plus } from 'lucide-react'
import api from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import { useLanguage } from '../../context/LanguageContext'
import ChatWithProvider from '../../components/ChatWithProvider'

export default function CustomerDashboard() {
  const { t } = useLanguage()
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('active')

  useEffect(() => {
    loadBookings()
  }, [activeTab])

  const loadBookings = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/bookings/my', {
        params: {
          status: activeTab === 'active' ? undefined : 'completed',
          page: 1,
          per_page: 10
        }
      })
      const bookings = 
        response.data?.data?.bookings ||
        response.data?.bookings ||
        response.data?.data ||
        response.data ||
        []
      setBookings(Array.isArray(bookings) ? bookings : [])
    } catch (error) {
      console.error('Failed to load bookings:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'pending': return 'bg-yellow-100 text-yellow-700'
      case 'confirmed': return 'bg-blue-100 text-blue-700'
      case 'in_progress': return 'bg-purple-100 text-purple-700'
      case 'completed': return 'bg-green-100 text-green-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">सेवा खरिद डैशबोर्ड</h1>
        <p className="text-gray-600 mb-8">नमस्ते, {user?.name}!</p>

        {/* Tabs */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab('active')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              activeTab === 'active' 
                ? 'bg-primary-700 text-white' 
                : 'bg-white border border-gray-300 text-gray-700'
            }`}
          >
            {t('activeBookings')}
          </button>
          <button
            onClick={() => setActiveTab('completed')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              activeTab === 'completed' 
                ? 'bg-primary-700 text-white' 
                : 'bg-white border border-gray-300 text-gray-700'
            }`}
          >
            {t('pastBookings')}
          </button>
        </div>

        {/* Bookings */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-12 h-12 border-4 border-primary-300 border-t-primary-700 rounded-full animate-spin"></div>
          </div>
        ) : bookings.length > 0 ? (
          <div className="space-y-4">
            {bookings.map((booking) => (
              <div key={booking.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">{booking.service?.title}</h3>
                    <p className="text-gray-600">बुकिङ क्र: #{booking.id}</p>
                  </div>
                  <span className={`px-4 py-2 rounded-full font-semibold text-sm ${getStatusColor(booking.status)}`}>
                    {booking.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                <div className="grid md:grid-cols-4 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="text-primary-700" size={20} />
                    <div>
                      <p className="text-sm text-gray-600">मिति</p>
                      <p className="font-semibold">
                        {booking.scheduled_at ? new Date(booking.scheduled_at).toLocaleDateString('ne-NP') : 'तोकिएको छैन'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="text-primary-700" size={20} />
                    <div>
                      <p className="text-sm text-gray-600">स्थान</p>
                      <p className="font-semibold">{booking.address?.substring(0, 20)}...</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign className="text-primary-700" size={20} />
                    <div>
                      <p className="text-sm text-gray-600">मूल्य</p>
                      <p className="font-semibold">₨{booking.final_price}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Star className="text-primary-700" size={20} />
                    <div>
                      <p className="text-sm text-gray-600">स्थिति</p>
                      <p className="font-semibold">{booking.payment_status}</p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <ChatWithProvider booking={booking} provider={booking.provider_details} />
                  <button className="px-6 py-2 bg-primary-700 text-white rounded-lg font-semibold hover:bg-primary-800 transition-colors">
                    विस्तृत विवरण देखुन्नुहोस्
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-gray-600 text-lg mb-4">{t('noBookings')}</p>
            <a href="/services" className="inline-block px-6 py-3 bg-primary-700 text-white rounded-lg font-semibold hover:bg-primary-800">
              {t('bookService')}
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
