FROM node:12.11.1-alpine
LABEL mantainer=""

# Install required system packages
RUN npm install -g @angular/cli@11.2.11

# Create directoris
RUN mkdir /usr/app
COPY aod-fianzas /usr/app/
WORKDIR /usr/app

# Build and install components
RUN npm install
RUN node_modules/.bin/ng build --prod --base-href /servicios/alquileres/

# Expose the port
EXPOSE 4200

CMD ["npm", "start"]