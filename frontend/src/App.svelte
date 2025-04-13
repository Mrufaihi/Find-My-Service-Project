<script lang="ts">
	// IMPORTS
	import * as Alert from "$lib/components/ui/alert/index";
  import Button from "$lib/components/ui/button/button.svelte";
	import * as Card from "$lib/components/ui/card/index";
  import * as Carousel from "$lib/components/ui/carousel/index";
	import type { CarouselAPI } from "$lib/components/ui/carousel/context.js";
  import { Input } from "$lib/components/ui/input/index.js";
	import * as Select from "$lib/components/ui/select/index.js";
	// Define Selected type locally
	type Selected<T> = { value: T; label: string } | T | undefined;
	import { ModeWatcher } from "mode-watcher";
  import { Textarea } from "$lib/components/ui/textarea/index.js";
  import { Label } from "$lib/components/ui/label";
  import LocationView from "$lib/locationView.svelte";
  import { mcpService } from "./services/mcpService";
  
  let api: CarouselAPI;
  
  $: if (api) {
		pickedCategory = categories[api.selectedScrollSnap()].value;
  }


	// State variables for the search form
	let query = '';
	let location = '';
	let loading = false;
	let isMcpPowered = false;
	
	// Define proper types using JSDoc for Svelte compatibility
	/** @type {Array<{name: string, mentions: number, rating: number}>} */
	let results = [];
	
	/** @type {string[]} */
	let extractedNames = [];
	
	/** @type {string|null} */
	let error = null;

	/**
	 * Search for service providers using the backend API
	 * 
	 * This function:
	 * 1. Sets loading state
	 * 2. Calls the Django search endpoint with query and location
	 * 3. Updates the UI with the results
	 */
	async function searchServiceProviders() {
		loading = true;
		error = null;
		
		try {
			// Use the MCPService to search for providers
			const data = await mcpService.searchProviders(query, location, pickedCategory as string);
			
			// Update the UI with the results
			if (data.success) {
				results = data.providers;
				isMcpPowered = data.mcp_powered || false;
				extractedNames = data.extracted_names || [];
			} else {
				error = data.error || 'An unknown error occurred';
				results = [];
			}
		} catch (err) {
			error = 'Failed to connect to the server';
			results = [];
		} finally {
			loading = false;
		}
	}

	// Check for MCP connection on component load
	let mcpAvailable = false;
	
	async function checkMcpStatus() {
		mcpAvailable = await mcpService.checkConnection();
	}
	
	// Call the function when component mounts
	checkMcpStatus();

	const categories = [
		{ value: "general", label: "General 🌏" },
    { value: "handy", label: "Handy 👨🏽‍🔧" },
    { value: "medicine", label: "Medicine 🧑🏻‍⚕️" },
  ];

	let pickedCategory:Selected<string>= categories[0].value //shadcn type
	
	// Handle location selection from map
	function handleLocationChange(newLocation: string) {
		location = newLocation;
	}

	// todo Google Maps API key - hardcoded since env variables having issues
	const googleMapsApiKey = 'AIzaSyB2kxDjle7yKIVJjoNVKw5vMkENy9TljQQ';

	// Track current page - default to home
	let currentPage = 'home';

	// Navigation functions
	function navigateToHome() {
		currentPage = 'home';
	}

	function navigateToFavorites() {
		currentPage = 'favorites';
	}

	function navigateToSearch() {
		currentPage = 'search';
	}

	function navigateToLogin() {
		currentPage = 'login';
	}
</script>

<!-- Navbar -->
<header class="border-b border-border w-full">
  <div class="container flex items-center justify-between h-16 px-4">
    <!-- Logo/Icon -->
    <div class="flex items-center gap-2 font-semibold cursor-pointer" on:click={navigateToHome}>
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
      <span>FindMyService</span>
    </div>
    
    <!-- Navigation Links -->
    <nav class="flex gap-6">
      <Button variant="ghost" on:click={navigateToHome} class="font-medium" data-active={currentPage === 'home' ? 'true' : 'false'}>
        Home
      </Button>
      <Button variant="ghost" on:click={navigateToFavorites} class="font-medium" data-active={currentPage === 'favorites' ? 'true' : 'false'}>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path></svg>
        Favorites
      </Button>
      <Button variant="ghost" on:click={navigateToSearch} class="font-medium" data-active={currentPage === 'search' ? 'true' : 'false'}>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
        Search
      </Button>
    </nav>
    
    <!-- Login Button -->
    <Button variant="outline" on:click={navigateToLogin} class="font-medium" data-active={currentPage === 'login' ? 'true' : 'false'}>
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      Login
    </Button>
  </div>
</header>

{#if currentPage === 'home'}
<main class="container p-4 max-w-4xl flex flex-col gap-5 justify-center ">
	<ModeWatcher />

	<!-- map -->
	 <div class="h-100 w-full" id="map">

	 </div>

	<div class="mb-8 text-center">
		<h1 class="text-3xl font-bold mb-2">Find My Service</h1>
		{#if mcpAvailable}
			<div class="text-sm text-primary font-medium mb-2">Enhanced with AI-powered search</div>
		{/if}
	</div>

	<div>
		<!-- <Select.Root selected={pickedCategory} onSelectedChange={(value)=> pickedCategory= value}
		>
			<Select.Trigger class="w-[180px]">
				<Select.Value placeholder="Select a Category"  />
			</Select.Trigger>
			<Select.Content>
				<Select.Group>
					<Select.Label>Category</Select.Label>
					{#each categories as category}
						<Select.Item value={category.value} label={category.label}>
							{category.label}
							</Select.Item
						>
					{/each}
				</Select.Group>
			</Select.Content>
			<Select.Input name="favoriteFruit" />
		</Select.Root>	</div> -->
	
		<div class="flex flex-col items-center">
			<Label class="text-xl" for="categorySelect">Category</Label>
			<Carousel.Root id="categorySelect" bind:api 
			class="w-full max-w-xs">
				<Carousel.Content>
					{#each categories as category}
						<Carousel.Item>
							<div class="p-1">
								<Card.Root>
									<Card.Content
										class="flex aspect-square items-center justify-center p-6"
									>
										<span class="text-4xl font-semibold">{category.label}</span>
									</Card.Content>
								</Card.Root>
							</div>
						</Carousel.Item>
					{/each}
				</Carousel.Content>
				<Carousel.Previous />
				<Carousel.Next />
			</Carousel.Root>
			<!-- Just display if value bind is working -->
			<h1>{pickedCategory}</h1>
		</div>

	
	<!-- Search Form -->
	<div class="bg-card rounded-lg shadow-md p-6 mb-6">
		<div class="mb-4">
			<Label  for="problem" class="block text-xl font-medium text-foreground mb-1">What problem do you need help with?</Label>
			<Textarea 
				id="problem" 
				bind:value={query} 
				rows={4}
				placeholder="I need a dentist who specializes in root canals"/>
		</div>
		
		<div class="mb-6">
			<label for="location" class="block text-xl font-medium text-foreground mb-1">Your Location</label>
			
			<!-- Google Maps Location Picker -->
			<LocationView apiKey={googleMapsApiKey} onChange={handleLocationChange} />
			
			<!-- Location Input Field (populated by map) -->
			<Input 
				id="location" 
				type="text" 
				bind:value={location} 
				class="w-full p-3 mt-2 border border-input rounded-md focus:ring-ring focus:border-ring" 
				placeholder="Location will appear here" />
		</div>	
		
		<Button 
			on:click={searchServiceProviders} 
			disabled={loading || !query || !location}
			variant="default"
			class="flex gap-2 w-full disabled:opacity-50 disabled:cursor-not-allowed">
			{loading ? 'Searching...' : 'Find Service Providers'}
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="m11.271 11.978l3.872 3.873a.5.5 0 0 0 .708 0a.5.5 0 0 0 0-.708l-3.565-3.564c2.38-2.747 2.267-6.923-.342-9.532c-2.73-2.73-7.17-2.73-9.898 0s-2.728 7.17 0 9.9a6.96 6.96 0 0 0 4.949 2.05a.5.5 0 0 0 0-1a5.96 5.96 0 0 1-4.242-1.757a6.01 6.01 0 0 1 0-8.486a6.004 6.004 0 0 1 8.484 0a6.01 6.01 0 0 1 0 8.486a.5.5 0 0 0 .034.738"/></svg>
		</Button>
	</div>

	<!-- Error message (if any) -->
	{#if error}
		<div class="bg-destructive/20 border border-destructive text-destructive px-4 py-3 rounded mb-6">
			<p>{error}</p>
		</div>
	{/if}

	<!-- Results list -->
	{#if results.length > 0}
		<div class="bg-card rounded-lg shadow-md p-6">
			<div class="flex justify-between items-center mb-4">
				<h2 class="text-xl font-semibold">Recommended Service Providers</h2>
				{#if isMcpPowered}
					<span class="text-xs bg-primary/20 text-primary px-2 py-1 rounded-full">AI-powered</span>
				{/if}
			</div>
			<ul class="divide-y divide-border">
				{#each results as provider}
					<li class="py-4">
						<div class="flex justify-between">
							<h3 class="font-medium">{provider.name}</h3>
							<span class="text-primary font-medium">{provider.mentions} mentions</span>
						</div>
						<div class="flex items-center mt-1">
							<div class="flex text-amber-400">
								{'★'.repeat(Math.floor(provider.rating))}
								{'☆'.repeat(5 - Math.floor(provider.rating))}
							</div>
							<span class="text-muted-foreground ml-1">{provider.rating.toFixed(1)}</span>
						</div>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- Extracted names (for demo purposes) -->
	{#if extractedNames.length > 0 && !isMcpPowered}
		<div class="bg-card rounded-lg shadow-md p-6 mt-6">
			<h2 class="text-xl font-semibold mb-4">Extracted Names (Proof of Concept)</h2>
			<p class="text-sm text-muted-foreground mb-2">These are potential service provider names extracted from your query:</p>
			<ul class="list-disc list-inside">
				{#each extractedNames as name}
					<li>{name}</li>
				{/each}
			</ul>
		</div>
	{/if}
</main>
{:else if currentPage === 'favorites'}
<!-- Favorites Page -->
<main class="container p-4 max-w-4xl flex flex-col gap-5 justify-center">
  <div class="mb-8 text-center">
    <h1 class="text-3xl font-bold mb-2">My Favorites</h1>
    <p class="text-muted-foreground">Your saved service providers will appear here</p>
  </div>
  
  <div class="bg-card rounded-lg shadow-md p-6">
    <div class="flex justify-center items-center py-8">
      <div class="text-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-auto mb-4 text-muted-foreground"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path></svg>
        <h3 class="text-xl font-medium mb-2">No favorites yet</h3>
        <p class="text-muted-foreground mb-4">Save your favorite service providers for quick access</p>
        <Button variant="outline" on:click={navigateToHome}>Find Services</Button>
      </div>
    </div>
  </div>
</main>
{:else if currentPage === 'search'}
<!-- Search History Page -->
<main class="container p-4 max-w-4xl flex flex-col gap-5 justify-center">
  <div class="mb-8 text-center">
    <h1 class="text-3xl font-bold mb-2">Search History</h1>
    <p class="text-muted-foreground">Your recent searches</p>
  </div>
  
  <div class="bg-card rounded-lg shadow-md p-6">
    <div class="flex justify-center items-center py-8">
      <div class="text-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-auto mb-4 text-muted-foreground"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
        <h3 class="text-xl font-medium mb-2">No search history</h3>
        <p class="text-muted-foreground mb-4">Your search history will appear here</p>
        <Button variant="outline" on:click={navigateToHome}>Start Searching</Button>
      </div>
    </div>
  </div>
</main>
{:else if currentPage === 'login'}
<!-- Login Page -->
<main class="container p-4 max-w-4xl flex flex-col gap-5 justify-center">
  <div class="mb-8 text-center">
    <h1 class="text-3xl font-bold mb-2">Login</h1>
    <p class="text-muted-foreground">Sign in to your account</p>
  </div>
  
  <Card.Root class="max-w-md mx-auto">
    <Card.Header>
      <Card.Title>Welcome Back</Card.Title>
      <Card.Description>Enter your credentials to access your account</Card.Description>
    </Card.Header>
    <Card.Content>
      <form class="space-y-4">
        <div class="space-y-2">
          <Label for="email">Email</Label>
          <Input id="email" type="email" placeholder="your.email@example.com" />
        </div>
        <div class="space-y-2">
          <Label for="password">Password</Label>
          <Input id="password" type="password" placeholder="••••••••" />
        </div>
        <Button type="button" class="w-full">Sign in</Button>
      </form>
    </Card.Content>
    <Card.Footer class="flex justify-center">
      <p class="text-sm text-muted-foreground">Don't have an account? <span class="text-primary cursor-pointer font-medium">Sign up</span></p>
    </Card.Footer>
  </Card.Root>
</main>
{/if}
