/**
 * MCPService - Client service for MCP-enabled backend
 *
 * This service handles communication with the Django backend's MCP functionality,
 * allowing the frontend to access AI-powered tools and search capabilities.
 */
export class MCPService {
  private apiUrl: string;
  private isConnected: boolean = false;

  constructor() {
    // Get backend URL from environment or use default
    this.apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    console.log('MCPService initialized with URL:', this.apiUrl);
  }

  /**
   * Check if MCP backend is available
   */
  async checkConnection(): Promise<boolean> {
    try {
      console.log('Checking MCP connection...');
      const response = await fetch(`${this.apiUrl}/search/?query=test&location=test`);
      console.log('Connection check response:', response.status, response.statusText);
      if (!response.ok) {
        this.isConnected = false;
        return false;
      }

      const data = await response.json();
      console.log('Connection check data:', data);
      // Check if the response has mcp_powered flag
      this.isConnected = data.hasOwnProperty('mcp_powered');
      return this.isConnected;
    } catch (error) {
      console.error('Error checking MCP connection:', error);
      this.isConnected = false;
      return false;
    }
  }

  /**
   * Search for service providers using MCP-powered backend
   *
   * @param query - User's service request/question
   * @param location - Geographic location for the search
   * @param category - Service category
   * @returns Search results
   */
  async searchProviders(
    query: string,
    location: string,
    category: string = 'general'
  ): Promise<any> {
    try {
      // Build search URL with all parameters
      const searchUrl = `${this.apiUrl}/search/?query=${encodeURIComponent(query)}&location=${encodeURIComponent(location)}&category=${encodeURIComponent(category)}`;
      console.log('Sending search request to:', searchUrl);

      // Make the request to backend
      const response = await fetch(searchUrl);
      console.log('Search response status:', response.status, response.statusText);

      if (!response.ok) {
        throw new Error(`Search request failed with status: ${response.status}`);
      }

      // Parse and return results
      const data = await response.json();
      console.log('Search response data:', data);
      return data;
    } catch (error) {
      console.error('Error searching providers:', error);
      throw error;
    }
  }

  /**
   * Check if connected to MCP backend
   */
  isBackendConnected(): boolean {
    return this.isConnected;
  }
}

// Create a singleton instance
export const mcpService = new MCPService();
