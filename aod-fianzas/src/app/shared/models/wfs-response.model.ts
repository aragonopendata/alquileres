export interface WFSResponse {
    crs: CRS
    features: Feature[]
    fotalFeatures: number
    type: string
}

interface CRS {
    type: string
    properties: CRSProperties[]
}

interface CRSProperties {
    name: string
}

interface Feature {
    geometry: object
    geometry_name: string
    id: string
    properties: FeatureProperties
    type: string
}

interface FeatureProperties {
    c_mun_via: string
    objectid: number
    valores: string
    via_loc: string
}
