import React from 'react'
import { Link } from 'react-router-dom'
import { Star, MapPin, Heart } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

export default function ProviderCard({ provider, user }) {
  const { t } = useLanguage()
  return (
    <div className="provider-card-hover bg-white rounded-lg overflow-hidden border border-gray-200">
      {/* Provider Photo */}
      <div className="relative h-48 bg-gradient-to-br from-primary-100 to-primary-200">
        {user?.profile_photo ? (
          <img src={user.profile_photo} alt={user?.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-primary-700">
            <span className="text-6xl">👤</span>
          </div>
        )}
        
        {/* Women First Badge */}
        {user?.is_female && (
          <div className="absolute top-2 right-2 women-first-badge">
            <span>💜 {t('womenFirst')}</span>
          </div>
        )}
        
        {/* Trust Badge */}
        {provider?.trust_badge && (
          <div className="absolute top-2 left-2 trust-badge">
            {provider.trust_badge}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Name and Location */}
        <h3 className="font-bold text-lg text-gray-800">{user?.name}</h3>
        <div className="flex items-center gap-1 text-gray-600 text-sm mb-3">
          <MapPin size={16} />
          <span>{user?.city}</span>
        </div>

        {/* Rating */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center bg-yellow-50 px-2 py-1 rounded">
            <Star size={16} className="text-yellow-500 fill-yellow-500" />
            <span className="ml-1 font-semibold text-gray-800">{provider?.rating || 0}</span>
          </div>
          <span className="text-gray-600 text-sm">({provider?.total_jobs || 0} jobs)</span>
        </div>

        {/* Skills */}
        <div className="mb-3">
          <div className="flex flex-wrap gap-1">
            {provider?.skills?.slice(0, 3).map((skill, idx) => (
              <span key={idx} className="bg-primary-100 text-primary-700 text-xs px-2 py-1 rounded">
                {skill}
              </span>
            ))}
          </div>
        </div>

        {/* Price */}
        {provider?.hourly_rate && (
          <p className="text-primary-700 font-semibold mb-3">
            ₨{provider.hourly_rate}/hour
          </p>
        )}

        {/* Buttons */}
        <div className="flex gap-2">
          <Link
            to={`/provider/${provider?.id}`}
            className="flex-1 px-3 py-2 bg-primary-100 text-primary-700 rounded-lg font-semibold hover:bg-primary-200 transition-colors text-sm text-center"
          >
            {t('viewProfile')}
          </Link>
          <Link
            to="/booking"
            className="flex-1 px-3 py-2 bg-primary-700 text-white rounded-lg font-semibold hover:bg-primary-800 transition-colors text-sm text-center"
          >
            {t('bookNow')}
          </Link>
        </div>
      </div>
    </div>
  )
}
