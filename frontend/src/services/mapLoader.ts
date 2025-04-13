//Module state
let loaded = false;
let loadPromise: Promise<void> = null;

// load google maps once
export function loadApi(apiKey: string): Promise<void> {
  // return existing promise if already looking
  if (loadPromise) return loadPromise;

  // return resolved promise if already loaded
  if (loaded) return Promise.resolve();

  // Create new load promise
  loadPromise = new Promise((resolve, reject) => {
    // if script already exists in DOM, API might be loading
    if (document.getElementById('google-maps-script')) {
      if (window.google?.maps) {
        loaded = true;
        resolve();
      } else {
        // wait for existing script to load
        window.addEventListener('google-maps-loaded', () => {
          loaded = true;
          resolve();
        });
      }
      return;
    }

    // Create callback function on window
    const callbackName = 'googleMapsLoaded';
    window[callbackName] = () => {
      loaded = true;
      window.dispatchEvent(new Event('google-maps-loaded'));
      resolve();
    };

    // create script element
    const script = document.createElement('script');
    script.id = 'google-maps-script';
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=${callbackName}`;
    script.async = true;
    script.onerror = reject;

    // append script to document
    document.head.appendChild(script);
  });

  return loadPromise;
}
