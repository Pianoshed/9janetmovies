export interface DownloadLink {
    label: string
    url: string
    host: string
}

export interface Movie {
    id: number
    title: string
    slug: string
    poster_url: string | null
    year: number
    genre: string
    description: string
    is_trending: boolean
    badge: 'NEW' | 'HOT' | 'CAM' | 'HD' | '' | null
    created_at: string
    links: DownloadLink[]
}

export interface Series {
    id: number
    title: string
    slug: string
    poster_url: string | null
    genre: string
    description: string
    created_at: string
    episodes: Episode[]
}

export interface Episode {
    season: number
    episode: number
    title: string
    url: string
    host: string
}

export interface MoviesResponse {
    movies: Movie[]
    total: number
    pages: number
    current: number
}