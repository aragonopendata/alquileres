import { Injectable } from '@angular/core';
import { Map, Overlay, View } from 'ol';
import { TileWMS } from 'ol/source';
import VectorSource from 'ol/source/Vector';
import { boundingExtent } from 'ol/extent';
import Projection from 'ol/proj/Projection';
import TileLayer from 'ol/layer/Tile';
import { GeoJSON } from 'ol/format';
import VectorLayer from 'ol/layer/Vector';
import { environment } from 'src/environments/environment';
import { Coordinate } from 'ol/coordinate';
import { Style, Stroke } from 'ol/style';
import { WFSResponse } from '../models/wfs-response.model';

@Injectable({
  providedIn: 'root'
})
export class MapService {

  constructor() { }

  /**
   *
   * @ngdoc method
   * @name MapService.initMap
   * @description Inicia el mapa de Aragón
   * @param {string=} target
   * @returns {Map=}
   */
  initMap(target: string, overlay: Overlay): Map {
    const extent = boundingExtent(environment.aragonBoundingBox);
    const projection = new Projection({
      code: environment.epsgCode,
      units: 'm'
    });
    const options = {
      projection: projection,
    };
    const layer = new TileLayer({
      source: new TileWMS({
        url: environment.urlWMSServer,
        params: {
          LAYERS: environment.wmsLayers,
          VERSION: environment.wmsVersion
        },
        projection: projection
      })
    });
    const olMap = new Map({
      target: target,
      view: new View(options),
      overlays: [overlay],
    });
    olMap.addLayer(layer);
    olMap.updateSize();
    olMap.getView().fit(extent);
    return olMap;
  }

  /**
   *
   * @ngdoc method
   * @name MapService.addLayer
   * @description Agrega una nueva capa al mapa a partir de la respuesta del servicio WFS
   * @param {Map=} olMap
   * @param {string=} capa
   * @param {WFSResponse=} wfsResponse
   */
  addLayer(olMap: Map, capa: string, wfsResponse: WFSResponse) {
    const className = `${capa}-layer`;
    const extent = boundingExtent(this.getBBox(wfsResponse.features));

    const geojsonFormat = new GeoJSON();

    try {
      const features = geojsonFormat.readFeatures(JSON.stringify(wfsResponse));

      const vectorLayer = new VectorLayer({
        source: new VectorSource({
          format: geojsonFormat,
          features: features,
        }),
        style: new Style({
          stroke: new Stroke({
            color: 'blue',
            width: 3
          })
        }),
        className: className
      });

      olMap.getLayers().getArray().filter(layer => layer.getClassName() === className)
        .forEach(layer => olMap.removeLayer(layer));

      olMap.addLayer(vectorLayer);

      olMap.getView().fit(extent);

    } catch (error) {
      console.error("Error processing features:", error);
    }
  }





  /**
   *
   * @ngdoc method
   * @name MapService.getBBox
   * @description Obtiene el boundingbox a partir de la geometría de la búsqueda
   * @param {any=} features
   * @returns {Coordinate=}
   */
  getBBox(features: any): Coordinate[] {
    // Handle empty/invalid input
    if (!features || features.length === 0) {
      return environment.aragonBoundingBox; // Fallback to default view
    }

    // Initialize with Aragon bounding box limits instead of Infinity
    const aragonBounds = environment.aragonBoundingBox;
    let minX = aragonBounds[1][0]; // Start with max X from Aragon
    let maxX = aragonBounds[0][0]; // Start with min X from Aragon
    let minY = aragonBounds[1][1]; // Start with max Y from Aragon
    let maxY = aragonBounds[0][1]; // Start with min Y from Aragon

    for (const feature of features) {
      if (!feature.geometry) {
        continue; // Skip features without geometry
      }

      // Extract coordinates from ANY geometry type
      const coords = this.extractCoordinatesFromGeometry(feature.geometry);

      for (const coord of coords) {
        if (coord.length >= 2) {
          const x = coord[0];
          const y = coord[1];

          minX = Math.min(minX, x);
          maxX = Math.max(maxX, x);
          minY = Math.min(minY, y);
          maxY = Math.max(maxY, y);
        }
      }
    }

    // Fallback if no valid coordinates found (bounds haven't changed from initial values)
    if (minX === aragonBounds[1][0] && maxX === aragonBounds[0][0] &&
        minY === aragonBounds[1][1] && maxY === aragonBounds[0][1]) {
      return environment.aragonBoundingBox;
    }

    return [[minX, minY], [maxX, maxY]];
  }

  /**
   * Helper method to extract coordinates from LineString and MultiLineString geometries only
   */
  private extractCoordinatesFromGeometry(geometry: any): number[][] {
    const coordinates: number[][] = [];

    switch (geometry.type) {
      case 'LineString':
        coordinates.push(...geometry.coordinates);
        break;

      case 'MultiLineString':
        for (const lineString of geometry.coordinates) {
          coordinates.push(...lineString);
        }
        break;

      // All other geometry types are ignored
      default:
        // Skip unsupported geometry types
        break;
    }

    return coordinates;
  }
}

