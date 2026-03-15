import { useState, useRef } from 'react'
import client from '../api/client'

export default function PhotoUpload({ currentPhoto, onUpload, size = 'lg' }) {
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState(currentPhoto)
  const fileRef = useRef(null)

  const sizes = {
    sm: 'w-12 h-12',
    md: 'w-20 h-20', 
    lg: 'w-32 h-32',
    xl: 'w-40 h-40'
  }

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Preview
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(file)

    // Upload
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('photo', file)
      const res = await client.post('/api/auth/upload-photo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      const photoUrl = res.data?.data?.photo_url
      if (onUpload) {
        onUpload(photoUrl)
      }
      // Give backend time to complete the transaction
      await new Promise(resolve => setTimeout(resolve, 500))
    } catch (err) {
      console.error('Upload failed:', err)
      setPreview(currentPhoto) // Revert preview on error
      alert('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="relative inline-block">
      <div
        className={`${sizes[size]} rounded-full overflow-hidden border-4 
                   border-purple-200 shadow-lg cursor-pointer relative group`}
        onClick={() => fileRef.current?.click()}
      >
        {preview ? (
          <img src={preview} alt="Profile" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-purple-100 flex items-center 
                          justify-center text-purple-600 font-bold text-2xl">
            👤
          </div>
        )}
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 
                        transition-opacity flex items-center justify-center">
          <span className="text-white text-xs font-medium">
            {uploading ? '⏳' : '📷 Change'}
          </span>
        </div>
      </div>

      {/* Upload indicator */}
      {uploading && (
        <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-purple-600 
                        rounded-full flex items-center justify-center">
          <div className="w-3 h-3 border-2 border-white border-t-transparent 
                          rounded-full animate-spin" />
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  )
}
