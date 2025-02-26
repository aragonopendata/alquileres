FROM node:14 AS build

WORKDIR /app

COPY ./package.json .
COPY ./package-lock.json .

RUN npm install -g @angular/cli@12
RUN npm install

COPY . /app
RUN ng build --prod --base-href=/servicios/alquileres/


FROM nginx:alpine

COPY --from=build /app/dist/aod-fianzas /usr/share/nginx/html/servicios/alquileres

