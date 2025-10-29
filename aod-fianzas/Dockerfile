FROM node:20 AS build

WORKDIR /app

COPY ./package.json .
COPY ./package-lock.json .

RUN npm install -g @angular/cli@19
RUN npm install

COPY . /app
RUN ng build --configuration production --base-href=/servicios/alquileres/


FROM nginx:alpine

# Copy built application
COPY --from=build /app/dist/aod-fianzas/browser /usr/share/nginx/html/servicios/alquileres

# Copy entrypoint script for config selection
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set environment variable (can be overridden by docker-compose)
ENV ENVIRONMENT=production

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
