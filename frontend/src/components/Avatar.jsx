import React from 'react'

const Avatar = ({ provider, size = 'md' }) => {
  const sizes = { 
    sm: 'w-10 h-10', 
    md: 'w-16 h-16', 
    lg: 'w-24 h-24' 
  }
  
  const colors = [
    'bg-purple-200 text-purple-700',
    'bg-blue-200 text-blue-700',
    'bg-green-200 text-green-700',
    'bg-pink-200 text-pink-700',
    'bg-orange-200 text-orange-700',
  ]
  
  const colorIndex = provider?.id % colors.length || 0

  if (provider?.profile_photo) {
    return (
      <img
        src={provider.profile_photo}
        alt={provider.name}
        className={`${sizes[size]} rounded-full object-cover border-2 border-white shadow-md`}
      />
    )
  }

  return (
    <div className={`${sizes[size]} rounded-full ${colors[colorIndex]}
                    flex items-center justify-center font-bold shadow-md
                    border-2 border-white text-lg`}>
      {provider?.name?.charAt(0)?.toUpperCase() || '?'}
    </div>
  )
}

export default Avatar
