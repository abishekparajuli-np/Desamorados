import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export default function LocationPicker({ 
  onChange, 
  initialLat = 27.7172,
  initialLng = 85.3240,
  height = '400px'
}) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const [lat, setLat] = useState(initialLat);
  const [lng, setLng] = useState(initialLng);
  const [address, setAddress] = useState('Kathmandu, Nepal');
  const [loading, setLoading] = useState(false);

  // Reverse geocode using Nominatim (free, open-source)
  const reverseGeocode = async (latitude, longitude) => {
    setLoading(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
      );
      const data = await response.json();
      setAddress(data.address?.name || data.display_name || 'Location');
      
      if (onChange) {
        onChange({
          lat: latitude,
          lng: longitude,
          address: data.address?.name || data.display_name || 'Location'
        });
      }
    } catch (error) {
      console.error('Geocoding error:', error);
      if (onChange) {
        onChange({ lat: latitude, lng: longitude, address: 'Unknown location' });
      }
    }
    setLoading(false);
  };

  // Initialize map
  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [lng, lat],
      zoom: 13,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
      }),
      'top-right'
    );

    map.on('load', () => {
      // Add draggable marker
      const el = document.createElement('div');
      el.className = 'w-8 h-8 bg-purple-600 rounded-full shadow-lg cursor-move border-2 border-white flex items-center justify-center text-white text-lg';
      el.innerHTML = '📍';
      el.style.backgroundImage = `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/></svg>')`;
      
      const marker = new maplibregl.Marker({
        element: el,
        draggable: true
      })
        .setLngLat([lng, lat])
        .addTo(map);

      markerRef.current = marker;

      // Update address on marker drag end
      marker.on('dragend', () => {
        const { lng: newLng, lat: newLat } = marker.getLngLat();
        setLat(newLat);
        setLng(newLng);
        reverseGeocode(newLat, newLng);
      });

      // Update marker position on map click
      map.on('click', (e) => {
        marker.setLngLat([e.lngLat.lng, e.lngLat.lat]);
        setLat(e.lngLat.lat);
        setLng(e.lngLat.lng);
        reverseGeocode(e.lngLat.lat, e.lngLat.lng);
      });

      // Center map when user location is found
      map.on('geolocate', (data) => {
        const { latitude, longitude } = data.coords;
        map.flyTo({
          center: [longitude, latitude],
          zoom: 14
        });
        marker.setLngLat([longitude, latitude]);
        setLat(latitude);
        setLng(longitude);
        reverseGeocode(latitude, longitude);
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Use current location
  const handleUseMyLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          mapRef.current.flyTo({
            center: [longitude, latitude],
            zoom: 14
          });
          if (markerRef.current) {
            markerRef.current.setLngLat([longitude, latitude]);
          }
          setLat(latitude);
          setLng(longitude);
          reverseGeocode(latitude, longitude);
        },
        (error) => {
          console.error('Geolocation error:', error);
          alert('Unable to get your location. Please enable location services.');
        }
      );
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  };

  return (
    <div className="space-y-3">
      <div 
        ref={mapContainer} 
        className="w-full rounded-xl overflow-hidden shadow-lg border border-gray-300"
        style={{ height }}
      />
      
      <div className="flex gap-2">
        <button
          onClick={handleUseMyLocation}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     font-semibold text-sm transition"
        >
          📍 Use My Location
        </button>
        <div className="flex-1 px-4 py-2 bg-gray-100 rounded-lg border border-gray-300 flex items-center">
          <span className="text-sm text-gray-700">
            {loading ? '🔄 Getting address...' : address}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
          <span className="text-gray-600">Latitude</span>
          <p className="font-mono font-semibold text-gray-900">{lat.toFixed(4)}</p>
        </div>
        <div className="px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
          <span className="text-gray-600">Longitude</span>
          <p className="font-mono font-semibold text-gray-900">{lng.toFixed(4)}</p>
        </div>
      </div>

      <p className="text-xs text-gray-500 text-center">
        💡 Click on the map or drag the marker to select your location
      </p>
    </div>
  );
}
