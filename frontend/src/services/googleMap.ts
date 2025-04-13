// Jeddah location: lat: 21.492500 lng: 39.177570

// map state
let map = null;
let marker = null;
let geocoder = null;
let retryCount = 0;
const MAX_RETRIES = 2;

// Getter functions to access map instances from other components
export function getMapInstance() {
  return map;
}

export function getMarkerInstance() {
  return marker;
}

// Check if we're in a secure context (HTTPS or localhost)
export function checkSecureContext(): boolean {
  if (!window.isSecureContext) {
    return false;
  }
  return true;
}

// ini google maps and return promise when ready
export async function initMap(element: HTMLElement) {
  //create map centered on default location
  map = new google.maps.Map(element, {
    center: { lat: 21.597597, lng: 39.143894 }, //jeddah
    zoom: 2,
    mapTypeControl: false,
  });

  //create market for selected postion
  marker = new google.maps.Marker({
    map,
    draggable: true,
  });

  //init geocoder for address lookup
  geocoder = new google.maps.Geocoder();
}

// Check if it's a MacOS CoreLocation error
function isMacOSCoreLocationError(error) {
  // Check for specific error message
  return (
    error &&
    typeof error.message === 'string' &&
    (error.message.includes('CoreLocation') || error.code === 2)
  ); // POSITION_UNAVAILABLE
}

// Check if coordinates are invalid (0,0) - sometimes returned as a fallback
function isInvalidCoordinates(position) {
  if (!position || !position.coords) return true;

  // Check if the position is exactly at 0,0 (null island) which is unlikely to be real
  return position.coords.latitude === 0 && position.coords.longitude === 0;
}

// Direct API call to Google's Geolocation API
// This is more reliable than the browser's geolocation API on macOS
export async function getLocationByGoogleGeolocationAPI(): Promise<google.maps.LatLngLiteral> {
  try {
    // Get API key from environment variable
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      throw new Error('Google Maps API key not found in environment variables');
    }

    // Prepare the request body - set considerIp to boolean false to prevent IP-based fallbacks
    const requestBody: any = { considerIp: false };

    // Try to get WiFi information if the browser supports it
    if (navigator.permissions) {
      try {
        // Check if we can access WiFi networks (only supported in some browsers)
        const wifiPermission = await navigator.permissions.query({ name: 'network-state' as any });

        if (wifiPermission.state === 'granted') {
          // This is experimental and likely won't work in most browsers
          if ((navigator as any).connection && (navigator as any).connection.type === 'wifi') {
            // This is where we would add WiFi access points if the browser allowed it
          }
        }
      } catch (permErr) {
        // Continue without WiFi data
      }
    }

    // Make a direct request to the Google Geolocation API
    const response = await fetch(
      `https://www.googleapis.com/geolocation/v1/geolocate?key=${apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      }
    );

    // Handle 404 error explicitly - this means no cell towers or WiFi access points could be found
    if (response.status === 404) {
      throw new Error('No location data available from cell towers or WiFi');
    }

    if (!response.ok) {
      throw new Error(`Google Geolocation API responded with ${response.status}`);
    }

    const data = await response.json();

    if (data && data.location && data.location.lat && data.location.lng) {
      const coords = {
        lat: data.location.lat,
        lng: data.location.lng,
      };

      return coords;
    }

    throw new Error('Invalid response from Google Geolocation API');
  } catch (err) {
    throw err;
  }
}

//get user's current postion and center map there
export async function getCurrentLocation(): Promise<string> {
  // Reset retry count when starting fresh
  retryCount = 0;
  return attemptGetCurrentLocation();
}

// Separate function to allow for retries
async function attemptGetCurrentLocation(): Promise<string> {
  // First check if we're in a secure context
  if (!window.isSecureContext) {
    return Promise.reject('Geolocation requires HTTPS (secure context)');
  }

  return new Promise((resolve, reject) => {
    // if cant get geolocation (reject)
    if (!navigator.geolocation) {
      reject('Geolocation not supported');
      return;
    }

    const isMacOS = /Mac/i.test(navigator.userAgent);

    // Set up a timeout to handle silent failures (especially for macOS CoreLocation)
    let locationTimeout = null;

    // If we're on macOS, set up a timeout as a "dead-man's switch"
    // for silent CoreLocation failures
    if (isMacOS) {
      locationTimeout = setTimeout(() => {
        // Attempt IP-based fallback
        handleIPFallback();
      }, 10000); // 10 seconds timeout for silent failures
    }

    // Function to clear the timeout if we get a response
    const clearLocationTimeout = () => {
      if (locationTimeout) {
        clearTimeout(locationTimeout);
        locationTimeout = null;
      }
    };

    // Function to handle IP-based fallback
    const handleIPFallback = async () => {
      try {
        const ipLocation = await getLocationByIP();

        if (ipLocation && map && marker) {
          map.setCenter(ipLocation);
          map.setZoom(8); // Lower zoom for less precision
          marker.setPosition(ipLocation);

          const address = await getAddressFromCoords(ipLocation);
          resolve(address + ' (approximate location)');
          return true;
        }
      } catch (err) {
        // IP fallback failed
      }
      return false;
    };

    // Handle permission states more explicitly
    const handleSuccess = async (position) => {
      // Clear the timeout for silent failures
      clearLocationTimeout();

      // Check if the position is valid (not a default fallback)
      if (isInvalidCoordinates(position)) {
        handleError({
          code: 2, // POSITION_UNAVAILABLE
          message: 'Received invalid coordinates from geolocation service',
        });
        return;
      }

      const pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };

      // if we have both map and marker
      if (map && marker) {
        map.setCenter(pos);
        map.setZoom(10);
        marker.setPosition(pos);

        // get address from coordinates
        const address = await getAddressFromCoords(pos);
        resolve(address);
      } else {
        reject('Map not initialized properly');
      }
    };

    const handleError = async (error) => {
      // Clear the timeout for silent failures
      clearLocationTimeout();

      // For macOS CoreLocation errors, try IP-based fallback
      if (error.code === 2 || isMacOSCoreLocationError(error)) {
        const fallbackSucceeded = await handleIPFallback();
        if (fallbackSucceeded) return;
      }

      // Format user-friendly error messages if no fallback succeeded
      switch (error.code) {
        case 1: // PERMISSION_DENIED
          reject(
            'Location permission denied. Please allow location access in your browser settings.'
          );
          break;
        case 2: // POSITION_UNAVAILABLE
          reject(
            'Location information is unavailable. Please select a location manually on the map.'
          );
          break;
        case 3: // TIMEOUT
          reject(
            'The request to get user location timed out. Please check your connection and try again.'
          );
          break;
        default:
          reject(`Error getting location: ${error.message}`);
      }
    };

    // Request position with options optimized for platform
    const options = {
      enableHighAccuracy: !isMacOS, // Disable high accuracy on macOS (more reliable)
      timeout: 15000, // Timeout after 15 seconds
      maximumAge: isMacOS ? 60000 : 0, // Use cached positions on macOS, fresh on others
    };

    // Actually make the geolocation request
    navigator.geolocation.getCurrentPosition(handleSuccess, handleError, options);
  });
}

// get formatted address from coordinates
export async function getAddressFromCoords(coords: google.maps.LatLngLiteral): Promise<string> {
  // if no geocoder expection
  if (!geocoder) return `${coords.lat}, ${coords.lng}`;

  try {
    const response = await geocoder.geocode({ location: coords });
    return response.results[0]?.formatted_address || `${coords.lat}, ${coords.lng}`;
  } catch (err) {
    return `${coords.lat}, ${coords.lng}`;
  }
}

// Set up click handler on map
export function setupClickHandler(callback: (address: string) => void): void {
  if (!map) return;

  map.addListener('click', async (e: google.maps.MapMouseEvent) => {
    if (!e.latLng || !marker) return;

    marker.setPosition(e.latLng);
    const address = await getAddressFromCoords(e.latLng.toJSON());
    callback(address);
  });
}

// IP-based fallback geolocation when browser geolocation fails
export async function getLocationByIP(): Promise<google.maps.LatLngLiteral | null> {
  try {
    // Try ipapi.co service (no API key required)
    const response = await fetch('https://ipapi.co/json/');
    if (!response.ok) {
      throw new Error(`ipapi.co responded with ${response.status}`);
    }

    const data = await response.json();

    if (data && data.latitude && data.longitude) {
      return {
        lat: parseFloat(data.latitude),
        lng: parseFloat(data.longitude),
      };
    }
    return null;
  } catch (err) {
    return null;
  }
}

// List of major Saudi Arabian cities with coordinates
export const saudiCities = [
  { name: 'Riyadh', coords: { lat: 24.7136, lng: 46.6753 } },
  { name: 'Jeddah', coords: { lat: 21.4858, lng: 39.1925 } },
  { name: 'Mecca', coords: { lat: 21.3891, lng: 39.8579 } },
  { name: 'Medina', coords: { lat: 24.5247, lng: 39.5692 } },
  { name: 'Dammam', coords: { lat: 26.4207, lng: 50.0888 } },
  { name: 'Taif', coords: { lat: 21.2703, lng: 40.4158 } },
  { name: 'Tabuk', coords: { lat: 28.3835, lng: 36.566 } },
  { name: 'Buraydah', coords: { lat: 26.3292, lng: 43.9715 } },
  { name: 'Khobar', coords: { lat: 26.2172, lng: 50.1971 } },
  { name: 'Abha', coords: { lat: 18.2164, lng: 42.5053 } },
  { name: 'Najran', coords: { lat: 17.5656, lng: 44.2289 } },
  { name: 'Jubail', coords: { lat: 27.0174, lng: 49.5585 } },
  { name: 'Khamis Mushait', coords: { lat: 18.3, lng: 42.7333 } },
  { name: 'Yanbu', coords: { lat: 24.023, lng: 38.19 } },
  { name: 'Al Ahsa', coords: { lat: 25.3758, lng: 49.5975 } },
];

// Set location to a selected city
export function selectCity(cityName: string): Promise<string> {
  const city = saudiCities.find((c) => c.name === cityName);

  if (!city) {
    return Promise.reject('City not found');
  }

  if (map && marker) {
    map.setCenter(city.coords);
    map.setZoom(10);
    marker.setPosition(city.coords);
    return getAddressFromCoords(city.coords);
  } else {
    return Promise.reject('Map not initialized properly');
  }
}

// Search for a place using Google Places API
export async function searchPlace(query: string): Promise<string> {
  if (!map || !marker) {
    return Promise.reject('Map not initialized properly');
  }

  if (!geocoder) {
    return Promise.reject('Geocoder not initialized properly');
  }

  try {
    const response = await geocoder.geocode({ address: query });

    if (response.results && response.results.length > 0) {
      const location = response.results[0].geometry.location;
      const coords = {
        lat: location.lat(),
        lng: location.lng(),
      };

      map.setCenter(coords);
      map.setZoom(10);
      marker.setPosition(coords);

      return response.results[0].formatted_address;
    } else {
      return Promise.reject('No results found for this search');
    }
  } catch (err) {
    return Promise.reject(`Search failed: ${err.message}`);
  }
}
