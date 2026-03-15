import React, { createContext, useState, useContext } from 'react'
import api from '../api/client'

const BookingContext = createContext()

export const BookingProvider = ({ children }) => {
  const [bookingData, setBookingData] = useState({
    service_type: null,
    location: null,
    preferred_time: null,
    description: null,
    address: null,
    latitude: null,
    longitude: null,
    final_price: null,
    ai_extracted_data: {}
  })
  const [selectedProviders, setSelectedProviders] = useState([])
  const [currentStep, setCurrentStep] = useState(1)

  const updateBookingData = (updates) => {
    setBookingData(prev => ({ ...prev, ...updates }))
  }

  const setProviderMatches = (providers) => {
    setSelectedProviders(providers)
  }

  const createBooking = async (provider_id, service_id, scheduled_at) => {
    try {
      const response = await api.post('/api/bookings', {
        provider_id,
        service_id,
        scheduled_at,
        address: bookingData.address,
        latitude: bookingData.latitude,
        longitude: bookingData.longitude,
        description: bookingData.description,
        final_price: bookingData.final_price,
        ai_extracted_data: bookingData.ai_extracted_data
      })
      
      return { success: true, booking: response.data.data }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Booking creation failed' 
      }
    }
  }

  const resetBooking = () => {
    setBookingData({
      service_type: null,
      location: null,
      preferred_time: null,
      description: null,
      address: null,
      latitude: null,
      longitude: null,
      final_price: null,
      ai_extracted_data: {}
    })
    setSelectedProviders([])
    setCurrentStep(1)
  }

  return (
    <BookingContext.Provider value={{
      bookingData,
      selectedProviders,
      currentStep,
      updateBookingData,
      setProviderMatches,
      setCurrentStep,
      createBooking,
      resetBooking
    }}>
      {children}
    </BookingContext.Provider>
  )
}

export const useBooking = () => {
  const context = useContext(BookingContext)
  if (!context) {
    throw new Error('useBooking must be used within BookingProvider')
  }
  return context
}
