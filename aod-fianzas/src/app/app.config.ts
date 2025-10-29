import { ApplicationConfig, APP_INITIALIZER, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { BrowserModule } from '@angular/platform-browser';
import { ServiceWorkerModule } from '@angular/service-worker';

import { ConfigService } from './core/services/config.service';
import { environment } from '../environments/environment';
import RouteConfig from './routes';

/**
 * Factory function for APP_INITIALIZER
 * Loads runtime configuration before app bootstraps
 */
export function initializeApp(configService: ConfigService): () => Promise<void> {
  return () => configService.loadConfig();
}

/**
 * Application configuration with runtime config loading
 * Uses APP_INITIALIZER to ensure config is loaded before app starts
 */
export const appConfig: ApplicationConfig = {
  providers: [
    importProvidersFrom(
      BrowserModule,
      ServiceWorkerModule.register('ngsw-worker.js', {
        enabled: environment.production,
        registrationStrategy: 'registerWhenStable:30000'
      })
    ),
    provideHttpClient(withInterceptorsFromDi()),
    provideRouter(RouteConfig),
    {
      provide: APP_INITIALIZER,
      useFactory: initializeApp,
      deps: [ConfigService],
      multi: true
    }
  ]
};
