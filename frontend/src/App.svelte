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
  
  let api: CarouselAPI;
  
  $: if (api) {
		pickedCategory = categories[api.selectedScrollSnap()].value;
  }


	// State variables for the search form
	let query = '';
	let location = '';
	let loading = false;
	
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
			// Build the search URL with query parameters
			const searchUrl = `/search/?query=${encodeURIComponent(query)}&location=${encodeURIComponent(location)}`;
			
			// Call the backend API
			const response = await fetch(searchUrl);
			const data = await response.json();
			
			// Update the UI with the results
			if (data.success) {
				results = data.providers;
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
</script>

<main class="container p-4 max-w-4xl flex flex-col gap-5 justify-center ">
	<ModeWatcher />

	<!-- map -->
	 <div class="h-100 w-full" id="map">

	 </div>

	<div class="mb-8 text-center">
		<h1 class="text-3xl font-bold mb-2">Find My Service</h1>
		<!-- <div class="flex items-center gap-2">	
			<Input type="search" placeholder="Search for service provider Near you..."/>
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="m11.271 11.978l3.872 3.873a.5.5 0 0 0 .708 0a.5.5 0 0 0 0-.708l-3.565-3.564c2.38-2.747 2.267-6.923-.342-9.532c-2.73-2.73-7.17-2.73-9.898 0s-2.728 7.17 0 9.9a6.96 6.96 0 0 0 4.949 2.05a.5.5 0 0 0 0-1a5.96 5.96 0 0 1-4.242-1.757a6.01 6.01 0 0 1 0-8.486a6.004 6.004 0 0 1 8.484 0a6.01 6.01 0 0 1 0 8.486a.5.5 0 0 0 .034.738"/></svg>
		</div> -->

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
			<h2 class="text-xl font-semibold mb-4">Recommended Service Providers</h2>
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
	{#if extractedNames.length > 0}
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
