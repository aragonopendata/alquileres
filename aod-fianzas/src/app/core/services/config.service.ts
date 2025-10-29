import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

/**
 * Runtime configuration interface matching config.json structure
 */
export interface IgearServicesConfig {
  typedSearchUrl: string;
  spatialSearchUrl: string;
  sitaWmsUrl: string;
  visor2dUrl: string;
}

export interface AppConfig {
  apiUrl: string;
  environment: string;
  igearServices: IgearServicesConfig;
}

/**
 * ConfigService loads runtime configuration from JSON file before app initialization.
 * This allows a single build to work across dev/pre/prod environments.
 *
 * Configuration is loaded from config.json, which is:
 * - Committed to git with default local development settings
 * - Replaced at container start time by docker-entrypoint.sh based on ENVIRONMENT variable
 */
@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private config: AppConfig | null = null;
  private readonly CONFIG_URL = '/assets/config/config.json';

  constructor(private http: HttpClient) {}

  /**
   * Loads configuration from config.json.
   * Called by APP_INITIALIZER before app bootstraps.
   * @returns Promise that resolves when config is loaded
   */
  async loadConfig(): Promise<void> {
    try {
      this.config = await this.http.get<AppConfig>(this.CONFIG_URL).toPromise();
      console.log('✓ Runtime configuration loaded:', {
        environment: this.config.environment,
        apiUrl: this.config.apiUrl
      });
    } catch (error) {
      console.error('Failed to load runtime configuration, using defaults:', error);
      // Fallback to local development defaults if config fails to load
      this.config = {
        apiUrl: 'http://localhost:4202',
        environment: 'local',
        igearServices: {
          typedSearchUrl: 'https://idearagon.aragon.es/servicios/TypedSearchService',
          spatialSearchUrl: 'https://idearagon.aragon.es/servicios/SpatialSearchService',
          sitaWmsUrl: 'https://idearagon.aragon.es/servicios/SITA_WMS',
          visor2dUrl: 'https://idearagon.aragon.es/datos/catalogo2/servlet/VisorServlet2D'
        }
      };
    }
  }

  /**
   * Gets the complete configuration object
   */
  getConfig(): AppConfig {
    if (!this.config) {
      throw new Error('Configuration not loaded. Ensure APP_INITIALIZER is configured correctly.');
    }
    return this.config;
  }

  /**
   * Gets the backend API base URL
   */
  getApiUrl(): string {
    return this.getConfig().apiUrl;
  }

  /**
   * Gets the current environment name
   */
  getEnvironment(): string {
    return this.getConfig().environment;
  }

  /**
   * Gets IGEAR services configuration
   */
  getIgearServices(): IgearServicesConfig {
    return this.getConfig().igearServices;
  }

  /**
   * Gets IGEAR TypedSearch service URL
   */
  getTypedSearchUrl(): string {
    return this.getConfig().igearServices.typedSearchUrl;
  }

  /**
   * Gets IGEAR SpatialSearch service URL
   */
  getSpatialSearchUrl(): string {
    return this.getConfig().igearServices.spatialSearchUrl;
  }

  /**
   * Gets IGEAR SITA WMS service URL
   */
  getSitaWmsUrl(): string {
    return this.getConfig().igearServices.sitaWmsUrl;
  }

  /**
   * Gets IGEAR Visor2D service URL
   */
  getVisor2dUrl(): string {
    return this.getConfig().igearServices.visor2dUrl;
  }
}
