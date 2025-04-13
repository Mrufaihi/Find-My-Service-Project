<script lang="ts">
  // Imports
  import {onMount} from 'svelte'
  import {loadApi} from '../services/mapLoader'
  import {
    initMap, 
    setupClickHandler, 
    getCurrentLocation, 
    checkSecureContext, 
    getLocationByGoogleGeolocationAPI, 
    getAddressFromCoords, 
    getMapInstance, 
    getMarkerInstance,
    saudiCities,
    selectCity,
    searchPlace
  } from '../services/googleMap'
  import Button from '$lib/components/ui/button/button.svelte'

  // Props
  export let apiKey:string;
  export let onChange: (location:string)=>void;

// variables
let mapElement: HTMLElement;
let loading = true;
let error = "";
let isSecureContext = true;
let permissionStatus = 'pending'; // 'pending' | 'granted' | 'denied' | 'unavailable'
let showPermissionInstructions = false;
let isLocationUnavailable = false;
let usingApproximateLocation = false;
let retryCount = 0;
const MAX_RETRIES = 2;
let possibleIpBasedLocation = false;
let searchQuery = '';
let selectedCity = '';

// Jeddah coordinates (approximate)
const JEDDAH_LAT = 21.5;
const JEDDAH_LNG = 39.2;

// Function to check if coordinates are likely from Jeddah (IP-based)
function isLikelyJeddahCoordinates(lat: number, lng: number): boolean {
  // Calculate distance between the coordinates and Jeddah
  const latDiff = Math.abs(lat - JEDDAH_LAT);
  const lngDiff = Math.abs(lng - JEDDAH_LNG);
  
  // If we're within 0.5 degrees of Jeddah (roughly 50km)
  return latDiff < 0.5 && lngDiff < 0.5;
}

// Initialize map when component mounts
onMount(async ()=>{
  try{
      // Check for secure context first
      isSecureContext = checkSecureContext();
      if (!isSecureContext) {
        error = 'Geolocation requires HTTPS to work properly';
        loading = false;
        return;
      }
      
      // Load Google Maps API
      await loadApi(apiKey);

      // Initialize map 
      await initMap(mapElement);

      // Set up click handler
      setupClickHandler((address) => {
        onChange(address);
      });

      // Check permission status if possible
      if (navigator.permissions && navigator.permissions.query) {
        try {
          const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName });
          permissionStatus = result.state;
          
          // Listen for permission changes
          result.addEventListener('change', () => {
            permissionStatus = result.state;
          });
        } catch (err) {
          // Could not query geolocation permission status
        }
      }

      // Finish loading
      loading = false;
  } catch(err) {
    error = 'Failed to load map';
    loading = false;
  }
});

async function handleGetCurrentLocation() {
  try {
    loading = true;
    error = "";
    isLocationUnavailable = false;
    usingApproximateLocation = false;
    possibleIpBasedLocation = false;

    // Check if running on macOS
    const isMacOS = /Mac/i.test(navigator.userAgent);
    
    if (isMacOS) {
      try {
        // For macOS, use the direct Geolocation API first because it's more reliable
        
        // Call the Google Geolocation API directly
        const coords = await getLocationByGoogleGeolocationAPI();
        
        // Get map and marker instances from the service
        const map = getMapInstance();
        const marker = getMarkerInstance();
        
        // Check if coordinates are likely from Jeddah (IP-based)
        if (coords && isLikelyJeddahCoordinates(coords.lat, coords.lng)) {
          possibleIpBasedLocation = true;
          usingApproximateLocation = true;
        }
        
        // Center the map and set the marker
        if (coords && map && marker) {
          map.setCenter(coords);
          map.setZoom(possibleIpBasedLocation ? 6 : 8); // Less zoom if it's IP-based
          marker.setPosition(coords);
          
          // Get address from coordinates
          const address = await getAddressFromCoords(coords);
          onChange(address + (possibleIpBasedLocation ? ' (approximate IP-based location)' : ' (using Google location service)'));
          permissionStatus = 'granted';
          showPermissionInstructions = false;
          loading = false;
          return;
        }
      } catch (directApiError) {
        // Fall through to the regular geolocation method
      }
    }
    
    // If not on macOS or direct API failed, try the standard approach
    const address = await getCurrentLocation();
    
    // Check if this is an approximate location (from IP fallback)
    if (address.includes("approximate location")) {
      usingApproximateLocation = true;
    }
    
    onChange(address);
    permissionStatus = 'granted';
    showPermissionInstructions = false;
  } catch (err) {
    error = String(err);
    
    // Check for different error types
    if (String(err).includes('denied') || String(err).includes('PERMISSION_DENIED')) {
      permissionStatus = 'denied';
      showPermissionInstructions = false; // Don't automatically show instructions
    } else if (String(err).includes('unavailable') || String(err).includes('POSITION_UNAVAILABLE')) {
      isLocationUnavailable = true;
      permissionStatus = 'unavailable';
    }
  } finally {
    loading = false;
  }
}

// Function to toggle permission instructions visibility
function togglePermissionInstructions() {
  showPermissionInstructions = !showPermissionInstructions;
}

// Function to retry getting location
async function retryGetLocation() {
  if (retryCount < MAX_RETRIES) {
    retryCount++;
    error = "Retrying to get your location...";
    loading = true;
    
    // Wait a moment before retrying
    setTimeout(async () => {
      await handleGetCurrentLocation();
    }, 1500);
  } else {
    error = "We couldn't determine your location after multiple attempts. Please select a location manually on the map.";
  }
}

// Function to handle city selection
async function handleCitySelect(event) {
  const cityName = event.target.value;
  selectedCity = cityName;
  
  if (!cityName) return;
  
  try {
    loading = true;
    error = "";
    
    const address = await selectCity(cityName);
    onChange(address);
  } catch (err) {
    error = String(err);
  } finally {
    loading = false;
  }
}

// Function to handle place search
async function handlePlaceSearch() {
  if (!searchQuery.trim()) {
    error = "Please enter a search term";
    return;
  }
  
  try {
    loading = true;
    error = "";
    
    const address = await searchPlace(searchQuery);
    onChange(address);
  } catch (err) {
    error = String(err);
  } finally {
    loading = false;
  }
}
</script>
<main>
  <!-- container -->
  <div class="map-container">
    <!-- Map Element -->
    <div 
      bind:this={mapElement} 
      class="w-full h-60 rounded-md mb-2 bg-muted"
      class:opacity-50={loading}
    ></div>
    
    <!-- Search & City Selection -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
      <!-- City Selection Dropdown -->
      <div class="w-full">
        <label for="city-select" class="text-sm font-medium block mb-1">Select a Saudi City</label>
        <select 
          id="city-select"
          bind:value={selectedCity}
          on:change={handleCitySelect}
          class="w-full p-2 border rounded-md bg-background"
          disabled={loading}
        >
          <option value="">-- Select a city --</option>
          {#each saudiCities as city}
            <option value={city.name}>{city.name}</option>
          {/each}
        </select>
      </div>
      
      <!-- Place Search -->
      <div class="w-full">
        <label for="place-search" class="text-sm font-medium block mb-1">Search for a place</label>
        <div class="flex gap-2">
          <input 
            id="place-search"
            type="text" 
            bind:value={searchQuery}
            placeholder="Enter city, address, landmark..."
            class="flex-1 p-2 border rounded-md bg-background"
            disabled={loading}
          />
          <Button 
            on:click={handlePlaceSearch}
            variant="secondary"
            size="sm"
            disabled={loading || !searchQuery.trim()}
          >
            Search
          </Button>
        </div>
      </div>
    </div>
    
    <!-- Loading/Error Messages -->
    {#if loading}
      <div class="text-center py-2">
        {#if error}
          {error}
        {:else}
          Loading map...
        {/if}
      </div>
    {/if}
    
    {#if error && !loading}
      <div class="text-destructive py-2 mb-2">
        {error}
        
        <!-- Permission Denied Instructions Button -->
        {#if permissionStatus === 'denied'}
          <div class="mt-1 text-sm">
            You've denied permission to access your location. 
            <button 
              class="text-primary underline" 
              on:click={togglePermissionInstructions}
            >
              {showPermissionInstructions ? 'Hide instructions' : 'Show me how to reset permissions'}
            </button>
          </div>
        
        <!-- Location Unavailable Retry Button -->
        {:else if isLocationUnavailable}
          <div class="mt-1 text-sm">
            <button 
              class="text-primary underline" 
              on:click={retryGetLocation}
              disabled={retryCount >= MAX_RETRIES}
            >
              Try again
            </button> or select a location manually on the map.
            
            {#if navigator.userAgent.includes('Mac')}
              <div class="mt-1 text-xs opacity-80">
                macOS users: This is a common issue with macOS location services. Try selecting a location directly on the map.
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
    
    {#if usingApproximateLocation && !loading}
      <div class="bg-yellow-50 text-yellow-800 p-3 my-2 rounded-md text-sm">
        {#if possibleIpBasedLocation}
          <p><strong>Notice:</strong> We detected that your location appears to be from Jeddah, but you may actually be in AlBaha or another location. This happens when we can only determine your approximate location based on your internet provider.</p>
          <p class="mt-1">For accurate location, please click directly on the map to mark your actual location.</p>
        {:else}
          <p>Using approximate location based on your IP address. For better accuracy, please allow location access or select a location directly on the map.</p>
        {/if}
      </div>
    {/if}
    
    <!-- Permission Reset Instructions -->
    {#if showPermissionInstructions && permissionStatus === 'denied'}
      <div class="bg-muted p-3 my-2 rounded-md text-sm">
        <h3 class="font-medium mb-1">How to reset location permission:</h3>
        <h4 class="font-medium">Chrome/Arc/Edge:</h4>
        <ol class="list-decimal list-inside pl-2 mb-2">
          <li>Click the lock/info icon in the address bar</li>
          <li>Select "Site settings" or "Permissions"</li>
          <li>Find "Location" and change to "Allow"</li>
        </ol>
        <h4 class="font-medium">Or reset from Settings:</h4>
        <ol class="list-decimal list-inside pl-2">
          <li>Open Chrome settings</li>
          <li>Go to "Privacy and security" → "Site settings"</li>
          <li>Select "Location"</li>
          <li>Find this website and change permission</li>
        </ol>
        <p class="mt-2 italic">After changing settings, refresh the page and try again.</p>
      </div>
    {/if}
    
    <!-- MacOS Location Services Help -->
    {#if isLocationUnavailable && !showPermissionInstructions && navigator.userAgent.includes('Mac')}
      <div class="bg-muted p-3 my-2 rounded-md text-sm">
        <h3 class="font-medium mb-1">For macOS Users Experiencing Location Issues:</h3>
        <p>We're using an improved location service for macOS that should work better than the standard browser geolocation. If you're still experiencing issues, try these steps:</p>
        <ol class="list-decimal list-inside pl-2">
          <li>Make sure Wi-Fi is turned on - <span class="font-semibold">this is required even when using ethernet</span></li>
          <li>Open System Settings → Privacy & Security → Location Services</li>
          <li>Turn Location Services off and back on</li>
          <li>Find your browser in the list and ensure it's allowed</li>
          <li>Restart your browser and try again</li>
        </ol>
        <div class="mt-2 p-2 bg-blue-50 text-blue-800 rounded">
          <p class="text-xs font-medium">Why this happens: macOS uses Wi-Fi signals to determine location and sometimes has issues with the CoreLocation service. Our app now tries multiple location methods automatically to provide the best experience.</p>
        </div>
        <p class="mt-2 italic">Selecting a location directly on the map is always the most reliable option.</p>
      </div>
    {/if}
    
    <!-- Current Location Button -->
    <Button 
      on:click={handleGetCurrentLocation}
      variant="outline"
      disabled={loading || !isSecureContext}
      class="w-full flex justify-center items-center gap-2 mt-2">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
      Use my current location
    </Button>
    
    
    {#if permissionStatus === 'denied' && !loading && !showPermissionInstructions}
      <div class="text-sm text-center mt-2 text-muted-foreground">
        Location access is blocked. Check browser settings to change permission.
      </div>
    {/if}
  </div>
</main>