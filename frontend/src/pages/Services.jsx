import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Filter, X, Map, Grid } from 'lucide-react'
import ProviderCard from '../components/ProviderCard'
import ProvidersMap from '../components/ProvidersMap'
import api from '../api/client'

export default function Services() {
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState('list') // 'list' or 'map'
  const [selectedProvider, setSelectedProvider] = useState(null)
  const [searchParams] = useSearchParams()

  const [filters, setFilters] = useState({
    city: searchParams.get('city') || '',
    women_first: searchParams.get('women_first') === 'true',
    min_rating: 0,
    page: 1
  })

  useEffect(() => {
    loadProviders()
  }, [filters])

  const loadProviders = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/providers', {
        params: {
          city: filters.city || undefined,
          women_first: filters.women_first,
          min_rating: filters.min_rating,
          page: filters.page,
          per_page: 12
        }
      })
      const providers = 
        response.data?.data?.providers ||
        response.data?.providers ||
        response.data?.data ||
        response.data ||
        []
      setProviders(Array.isArray(providers) ? providers : [])
    } catch (error) {
      console.error('Failed to load providers:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleWomenFirst = () => {
    setFilters(prev => ({ ...prev, women_first: !prev.women_first, page: 1 }))
  }

  const cities = ['काठमाडौ', 'ललितपुर', 'भक्तपुर', 'पोखरा', 'वीरगंज']

  // Handle provider click on map
  const handleProviderClick = (providerId) => {
    const provider = providers.find(p => p.id === providerId || p.provider?.id === providerId)
    if (provider) setSelectedProvider(provider)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2 text-gray-800">सेवा प्रदान गर्नेहरू</h1>
            <p className="text-gray-600">नेपालमा हजारौ सेवा प्रदान गर्नेहरूबाट चुनौं</p>
          </div>
          
          {/* View Mode Toggle */}
          <div className="flex gap-2 bg-white rounded-lg shadow-md p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 rounded-md font-semibold flex items-center gap-2 transition ${
                viewMode === 'list'
                  ? 'bg-primary-700 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Grid size={18} />
              सूची
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`px-4 py-2 rounded-md font-semibold flex items-center gap-2 transition ${
                viewMode === 'map'
                  ? 'bg-primary-700 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Map size={18} />
              नक्शा
            </button>
          </div>
        </div>

        {viewMode === 'list' ? (
          // LIST VIEW
          <div className="flex gap-8">
            {/* Filters */}
            <div className={`${showFilters ? 'block' : 'hidden'} md:block md:w-64`}>
              <div className="bg-white rounded-lg shadow-md p-6 sticky top-20">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-lg">फिल्टरहरू</h3>
                  <button 
                    onClick={() => setShowFilters(false)}
                    className="md:hidden"
                  >
                    <X />
                  </button>
                </div>

                {/* Women First Toggle */}
                <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border-2 border-primary-300">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.women_first}
                      onChange={toggleWomenFirst}
                      className="w-5 h-5 accent-primary-700"
                    />
                    <span className="font-semibold text-primary-700">💜 महिला पहिले</span>
                  </label>
                </div>

                {/* City Filter */}
                <div className="mb-6">
                  <label className="block font-semibold mb-3">शहर</label>
                  <select
                    value={filters.city}
                    onChange={(e) => setFilters(prev => ({ ...prev, city: e.target.value, page: 1 }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">सबै शहरहरू</option>
                    {cities.map(city => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                </div>

                {/* Rating Filter */}
                <div className="mb-6">
                  <label className="block font-semibold mb-3">न्यूनतम रेटिङ</label>
                  <select
                    value={filters.min_rating}
                    onChange={(e) => setFilters(prev => ({ ...prev, min_rating: parseFloat(e.target.value), page: 1 }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="0">सबै</option>
                    <option value="3.5">3.5+ ⭐</option>
                    <option value="4">4+ ⭐</option>
                    <option value="4.5">4.5+ ⭐</option>
                  </select>
                </div>

                <button
                  onClick={() => {
                    setFilters({ city: '', women_first: false, min_rating: 0, page: 1 })
                  }}
                  className="w-full px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
                >
                  फिल्टरहरू रिसेट गर्नुहोस्
                </button>
              </div>
            </div>

            {/* Providers Grid */}
            <div className="flex-1">
              <button
                onClick={() => setShowFilters(true)}
                className="md:hidden mb-4 px-4 py-2 bg-primary-700 text-white rounded-lg flex items-center gap-2"
              >
                <Filter size={20} />
                फिल्टरहरू
              </button>

              {loading ? (
                <div className="text-center py-12">
                  <div className="inline-block w-12 h-12 border-4 border-primary-300 border-t-primary-700 rounded-full animate-spin"></div>
                </div>
              ) : providers.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {providers.map((provider) => (
                    <ProviderCard
                      key={provider.id}
                      provider={provider.provider}
                      user={provider}
                    />
                  ))}
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-12 text-center">
                  <p className="text-gray-600 text-lg">कोनै सेवा प्रदान गर्नेहरू नहिंसे।</p>
                  <p className="text-gray-500 mt-2">फिल्टरहरू परिवर्तन गर्न प्रयास गर्नुहोस्।</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          // MAP VIEW
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-300px)]">
            {/* Map */}
            <div className="lg:col-span-2 rounded-2xl overflow-hidden shadows-xl">
              {!loading && providers.length > 0 && (
                <ProvidersMap
                  showFemaleOnly={filters.women_first}
                  onProviderClick={handleProviderClick}
                  centerLat={27.7172}
                  centerLng={85.3240}
                  zoom={12}
                />
              )}
            </div>

            {/* Provider Details Panel */}
            <div className="bg-white rounded-xl shadow-lg p-6 overflow-y-auto">
              <div className="mb-4">
                <label className="flex items-center gap-3 cursor-pointer mb-6">
                  <input
                    type="checkbox"
                    checked={filters.women_first}
                    onChange={toggleWomenFirst}
                    className="w-5 h-5 accent-primary-700"
                  />
                  <span className="font-semibold text-primary-700">💜 महिला पहिले</span>
                </label>
              </div>

              {selectedProvider ? (
                <div>
                  <h3 className="text-xl font-bold mb-2">{selectedProvider.name}</h3>
                  {selectedProvider.provider && (
                    <>
                      <p className="text-sm text-gray-600 mb-4">{selectedProvider.provider.bio}</p>
                      <div className="space-y-3 mb-6">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">रेटिङ:</span>
                          <span className="font-semibold">⭐ {selectedProvider.provider.rating}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">विश्वास स्कोर:</span>
                          <span className="font-semibold">{selectedProvider.provider.trust_score}/100</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">घण्टाको दर:</span>
                          <span className="font-semibold">₹{selectedProvider.provider.hourly_rate}</span>
                        </div>
                      </div>
                      <button className="w-full px-4 py-2 bg-primary-700 text-white rounded-lg font-semibold hover:bg-primary-800 transition">
                        अहिले बुक गर्नुहोस्
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <p>नक्शामा सेवा प्रदान गर्नेलाई क्लिक गर्नुहोस्</p>
                  <p className="text-sm mt-2">विवरण यहाँ देखा पर्नेछ</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
