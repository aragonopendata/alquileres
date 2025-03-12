FROM node:20 AS build

WORKDIR /app

COPY ./package.json .
COPY ./package-lock.json .

RUN npm install -g @angular/cli@19
RUN npm install

COPY . /app
RUN ng build --configuration production --base-href=/servicios/alquileres/


FROM nginx:alpine

COPY --from=build /app/dist/aod-fianzas/browser /usr/share/nginx/html/servicios/alquileres

