import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { BookingProvider } from './context/BookingContext'

// Pages
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Services from './pages/Services'
import ProviderProfile from './pages/ProviderProfile'
import BookingFlow from './pages/BookingFlow'
import AdminDashboard from './pages/AdminDashboard'
import CustomerDashboard from './pages/Dashboard/CustomerDashboard'
import ProviderDashboard from './pages/Dashboard/ProviderDashboard'

// Components
import Navbar from './components/Navbar'
import ChatBot from './components/ChatBot'
import Loading from './components/Loading'

// Protected Route Component
function ProtectedRoute({ children, role }) {
  const { isAuthenticated, user, loading } = useAuth()

  if (loading) return <Loading />

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role && user?.role !== role) {
    return <Navigate to="/" replace />
  }

  return children
}

function AppContent() {
  const { loading } = useAuth()

  if (loading) return <Loading />

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      
      <main className="relative">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/services" element={<Services />} />
          <Route path="/provider/:id" element={<ProviderProfile />} />

          {/* Customer Routes */}
          <Route 
            path="/booking" 
            element={
              <ProtectedRoute role="customer">
                <BookingFlow />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/dashboard/customer" 
            element={
              <ProtectedRoute role="customer">
                <CustomerDashboard />
              </ProtectedRoute>
            } 
          />

          {/* Provider Routes */}
          <Route 
            path="/dashboard/provider" 
            element={
              <ProtectedRoute role="provider">
                <ProviderDashboard />
              </ProtectedRoute>
            } 
          />

          {/* Admin Routes */}
          <Route 
            path="/dashboard/admin" 
            element={
              <ProtectedRoute role="admin">
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Floating Chatbot */}
      <ChatBot />
    </div>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <BookingProvider>
          <AppContent />
        </BookingProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
