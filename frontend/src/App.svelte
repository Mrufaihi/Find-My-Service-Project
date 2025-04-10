<script lang="ts">
	// IMPORTS
	import * as Alert from "$lib/components/ui/alert/index";
  import Button from "$lib/components/ui/button/button.svelte";
	import * as Card from "$lib/components/ui/card/index";
  import * as Carousel from "$lib/components/ui/carousel/index";
  import { Input } from "$lib/components/ui/input/index.js";
	import * as Select from "$lib/components/ui/select/index.js";
	import { ModeWatcher } from "mode-watcher";



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
			console.error('Error searching providers:', err);
			error = 'Failed to connect to the server';
			results = [];
		} finally {
			loading = false;
		}
	}

	const categories = [
    { value: "handy", label: "Handy" },
    { value: "medicine", label: "Medicine" },
  ];
</script>

<main class="container p-4 max-w-4xl flex flex-col gap-5">
	<ModeWatcher />

	<div class="mb-8 text-center">
		<h1 class="text-3xl font-bold mb-2">Find My Service</h1>
		<div class="flex items-center gap-2">	
			<Input type="search" placeholder="Search for service provider Near you..."/>
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="m11.271 11.978l3.872 3.873a.5.5 0 0 0 .708 0a.5.5 0 0 0 0-.708l-3.565-3.564c2.38-2.747 2.267-6.923-.342-9.532c-2.73-2.73-7.17-2.73-9.898 0s-2.728 7.17 0 9.9a6.96 6.96 0 0 0 4.949 2.05a.5.5 0 0 0 0-1a5.96 5.96 0 0 1-4.242-1.757a6.01 6.01 0 0 1 0-8.486a6.004 6.004 0 0 1 8.484 0a6.01 6.01 0 0 1 0 8.486a.5.5 0 0 0 .034.738"/></svg>
		</div>
		<Button>HEY</Button>
	</div>

	<div>
		<Select.Root>
			<Select.Trigger class="w-[180px]">
				<Select.Value placeholder="Select a Category" />
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
		</Select.Root>	</div>
	<Carousel.Root class="w-full max-w-xs">
		<Carousel.Content>
			{#each Array(5) as _, i (i)}
				<Carousel.Item>
					<div class="p-1">
						<Card.Root>
							<Card.Content
								class="flex aspect-square items-center justify-center p-6"
							>
								<span class="text-4xl font-semibold">{i + 1}</span>
							</Card.Content>
						</Card.Root>
					</div>
				</Carousel.Item>
			{/each}
		</Carousel.Content>
		<Carousel.Previous />
		<Carousel.Next />
	</Carousel.Root>
	Copy
	About
	
	<!-- Search Form -->
	<div class="bg-white rounded-lg shadow-md p-6 mb-6">
		<div class="mb-4">
			<label for="problem" class="block text-sm font-medium text-gray-700 mb-1">What problem do you need help with?</label>
			<textarea 
				id="problem" 
				bind:value={query} 
				class="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" 
				rows="3" 
				placeholder="Describe your issue (e.g., 'I need a dentist who specializes in root canals')"></textarea>
		</div>
		
		<div class="mb-6">
			<label for="location" class="block text-sm font-medium text-gray-700 mb-1">Your Location</label>
			<input 
				id="location" 
				type="text" 
				bind:value={location} 
				class="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" 
				placeholder="City, State or Zip Code" />
		</div>
		
		<Button 
		 	variant="default"
			on:click={searchServiceProviders} 
			disabled={loading || !query || !location}
			class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed">
			{loading ? 'Searching...' : 'Find Service Providers'}
		</Button>
	</div>

	<!-- Error message (if any) -->
	{#if error}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
			<p>{error}</p>
		</div>
	{/if}

	<!-- Results list -->
	{#if results.length > 0}
		<div class="bg-white rounded-lg shadow-md p-6">
			<h2 class="text-xl font-semibold mb-4">Recommended Service Providers</h2>
			<ul class="divide-y divide-gray-200">
				{#each results as provider}
					<li class="py-4">
						<div class="flex justify-between">
							<h3 class="font-medium">{provider.name}</h3>
							<span class="text-blue-600 font-medium">{provider.mentions} mentions</span>
						</div>
						<div class="flex items-center mt-1">
							<div class="flex text-yellow-400">
								{'★'.repeat(Math.floor(provider.rating))}
								{'☆'.repeat(5 - Math.floor(provider.rating))}
							</div>
							<span class="text-gray-600 ml-1">{provider.rating.toFixed(1)}</span>
						</div>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- Extracted names (for demo purposes) -->
	{#if extractedNames.length > 0}
		<div class="bg-white rounded-lg shadow-md p-6 mt-6">
			<h2 class="text-xl font-semibold mb-4">Extracted Names (Proof of Concept)</h2>
			<p class="text-sm text-gray-600 mb-2">These are potential service provider names extracted from your query:</p>
			<ul class="list-disc list-inside">
				{#each extractedNames as name}
					<li>{name}</li>
				{/each}
			</ul>
		</div>
	{/if}
</main>

<style>
	:global(body) {
		background-color: #f9fafb;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
			Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
	}
</style>