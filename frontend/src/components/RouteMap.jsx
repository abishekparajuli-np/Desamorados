import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

export default function RouteMap({ providers = [], onProviderSelect }) {
  const mapContainer = useRef(null)
  const mapRef = useRef(null)
  const [customerLocation, setCustomerLocation] = useState(null)
  const [selectedProvider, setSelectedProvider] = useState(null)
  const [routeInfo, setRouteInfo] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Ask for customer location
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported')
      setLoading(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        }
        setCustomerLocation(loc)
        setLoading(false)
        initMap(loc)
      },
      (err) => {
        // Fallback to Kathmandu center if denied
        const fallback = { lat: 27.7172, lng: 85.3240 }
        setCustomerLocation(fallback)
        setLocationError('Using default location (Kathmandu)')
        setLoading(false)
        initMap(fallback)
      },
      { enableHighAccuracy: true, timeout: 8000 }
    )
  }, [])

  const initMap = (customerLoc) => {
    if (mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [customerLoc.lng, customerLoc.lat],
      zoom: 13,
    })

    map.addControl(new maplibregl.NavigationControl(), 'top-right')

    map.on('load', () => {
      // Add customer marker (blue)
      const customerEl = document.createElement('div')
      customerEl.innerHTML = `
        <div style="background:#3B82F6;width:40px;height:40px;border-radius:50%;
                    border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);
                    display:flex;align-items:center;justify-content:center;
                    font-size:18px;cursor:pointer">
          📍
        </div>
      `
      new maplibregl.Marker({ element: customerEl })
        .setLngLat([customerLoc.lng, customerLoc.lat])
        .setPopup(new maplibregl.Popup().setHTML(
          '<div style="font-family:Inter,sans-serif;padding:4px"><strong>📍 Your Location</strong></div>'
        ))
        .addTo(map)

      // Add provider markers (purple)
      providers.forEach((p) => {
        const provLat = p.latitude || p.provider?.latitude
        const provLng = p.longitude || p.provider?.longitude
        if (!provLat || !provLng) return

        const el = document.createElement('div')
        el.innerHTML = `
          <div style="background:${p.is_female ? '#7C3AED' : '#6366F1'};
                      width:36px;height:36px;border-radius:50%;
                      border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);
                      display:flex;align-items:center;justify-content:center;
                      font-size:16px;cursor:pointer;transition:transform 0.2s"
               onmouseover="this.style.transform='scale(1.2)'"
               onmouseout="this.style.transform='scale(1)'">
            ${p.is_female ? '💜' : '👤'}
          </div>
        `

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([provLng, provLat])
          .setPopup(
            new maplibregl.Popup({ offset: 25, maxWidth: '200px' })
              .setHTML(`
                <div style="font-family:Inter,sans-serif;padding:8px">
                  <strong>${p.name}</strong>
                  ${p.is_female ? '<span style="color:#7C3AED;font-size:11px"> 💜 Women First</span>' : ''}
                  <div style="font-size:12px;color:#6B7280">⭐ ${p.provider?.rating?.toFixed(1) || 'New'}</div>
                  <div style="font-size:12px;color:#6B7280">📍 ${p.city || 'Kathmandu'}</div>
                  <button 
                    onclick="window.dispatchEvent(new CustomEvent('selectProvider', {detail: '${p.id}'}))"
                    style="margin-top:6px;width:100%;padding:5px;background:#7C3AED;
                           color:white;border:none;border-radius:6px;cursor:pointer;
                           font-size:12px;font-weight:600">
                    🗺️ Show Route
                  </button>
                </div>
              `)
          )
          .addTo(map)
      })

      // Route source (empty initially)
      map.addSource('route', {
        type: 'geojson',
        data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] } }
      })

      map.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#7C3AED',
          'line-width': 4,
          'line-opacity': 0.8,
          'line-dasharray': [2, 1]
        }
      })
    })

    mapRef.current = map

    // Listen for provider selection
    const handleSelect = async (e) => {
      const providerId = e.detail
      const provider = providers.find(p => p.id === parseInt(providerId))
      if (provider) {
        setSelectedProvider(provider)
        await drawRoute(map, customerLoc, provider)
        if (onProviderSelect) onProviderSelect(provider)
      }
    }
    window.addEventListener('selectProvider', handleSelect)
    return () => window.removeEventListener('selectProvider', handleSelect)
  }

  const drawRoute = async (map, from, to) => {
    const toLat = to.latitude || to.provider?.latitude
    const toLng = to.longitude || to.provider?.longitude
    if (!toLat || !toLng) return

    try {
      // Use OSRM free routing (no API key needed!)
      const url = `https://router.project-osrm.org/route/v1/driving/${from.lng},${from.lat};${toLng},${toLat}?overview=full&geometries=geojson`
      const res = await fetch(url)
      const data = await res.json()

      if (data.routes && data.routes.length > 0) {
        const route = data.routes[0]
        const coords = route.geometry.coordinates

        // Update route line on map
        map.getSource('route').setData({
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: coords }
        })

        // Fit map to show full route
        const bounds = coords.reduce(
          (b, c) => b.extend(c),
          new maplibregl.LngLatBounds(coords[0], coords[0])
        )
        map.fitBounds(bounds, { padding: 60 })

        // Set route info
        const distanceKm = (route.distance / 1000).toFixed(1)
        const durationMin = Math.round(route.duration / 60)
        setRouteInfo({
          distance: distanceKm,
          duration: durationMin,
          provider: to.name
        })
      }
    } catch (err) {
      console.error('Routing failed:', err)
      // Fallback: draw straight line
      const coords = [[from.lng, from.lat], [toLng, toLat]]
      map.getSource('route').setData({
        type: 'Feature',
        geometry: { type: 'LineString', coordinates: coords }
      })
      const dist = haversineDistance(from.lat, from.lng, toLat, toLng)
      setRouteInfo({
        distance: dist.toFixed(1),
        duration: Math.round(dist * 3),
        provider: to.name,
        isStraightLine: true
      })
    }
  }

  const haversineDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLng = (lng2 - lng1) * Math.PI / 180
    const a = Math.sin(dLat/2) ** 2 +
              Math.cos(lat1 * Math.PI/180) *
              Math.cos(lat2 * Math.PI/180) *
              Math.sin(dLng/2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  }

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center 
                      bg-gray-50 rounded-2xl">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-3">🗺️</div>
          <p className="text-gray-600">Getting your location...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-xl">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Location error banner */}
      {locationError && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 
                        bg-yellow-50 border border-yellow-200 rounded-xl 
                        px-4 py-2 text-xs text-yellow-700 shadow-md z-10">
          ⚠️ {locationError}
        </div>
      )}

      {/* Route info card */}
      {routeInfo && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 
                        bg-white rounded-2xl shadow-xl p-4 z-10 
                        min-w-64 border border-purple-100">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-purple-600 font-bold text-sm">
              🗺️ Route to {routeInfo.provider}
            </span>
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-700">
                {routeInfo.distance}
              </div>
              <div className="text-xs text-gray-500">km away</div>
            </div>
            <div className="w-px bg-gray-200"/>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {routeInfo.duration}
              </div>
              <div className="text-xs text-gray-500">min drive</div>
            </div>
            <div className="w-px bg-gray-200"/>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {routeInfo.isStraightLine ? '~' : ''}
                {Math.round(routeInfo.distance * 12)}
              </div>
              <div className="text-xs text-gray-500">min walk</div>
            </div>
          </div>
          {routeInfo.isStraightLine && (
            <p className="text-xs text-gray-400 mt-2 text-center">
              * Approximate straight-line distance
            </p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm 
                      rounded-xl p-3 shadow-md text-xs space-y-1 z-10">
        <div className="flex items-center gap-2">
          <span className="text-base">📍</span>
          <span className="text-gray-600">Your location</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-base">💜</span>
          <span className="text-gray-600">Women First</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-base">👤</span>
          <span className="text-gray-600">Provider</span>
        </div>
        <div className="flex items-center gap-2 pt-1 border-t border-gray-100">
          <div className="w-6 h-1 bg-purple-600 rounded"/>
          <span className="text-gray-600">Route</span>
        </div>
      </div>
    </div>
  )
}
