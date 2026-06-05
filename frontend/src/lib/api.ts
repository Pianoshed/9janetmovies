import { Movie, MoviesResponse, Series } from './types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000/api'
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY

async function fetchJSON<T>(url: string): Promise<T | null> {
    const res = await fetch(url, {
        cache: 'no-store',
        headers: {
            ...(INTERNAL_API_KEY && { 'X-Internal-Key': INTERNAL_API_KEY }),
        },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
}

export async function getMovies(page = 1, genre = ''): Promise<MoviesResponse> {
    try {
        const url = genre
            ? `${API}/movies?page=${page}&genre=${encodeURIComponent(genre)}`
            : `${API}/movies?page=${page}`
        const data = await fetchJSON<any>(url)
        return {
            movies: data?.movies ?? [],
            total: data?.total ?? 0,
            pages: data?.pages ?? 0,
            current: data?.current ?? page,
        }
    } catch (err) {
        console.error('getMovies error:', err)
        return { movies: [], total: 0, pages: 0, current: page }
    }
}

export async function getAllSeries(): Promise<Series[]> {
    try {
        // No page param → Flask returns all series in one shot
        // (frontend handles its own pagination)
        const data = await fetchJSON<any>(`${API}/series`) ?? {}
        return data?.series ?? []
    } catch (err) {
        console.error('getAllSeries error:', err)
        return []
    }
}

export async function getSeries(slug: string): Promise<Series | null> {
    try {
        if (!slug) return null
        return await fetchJSON<Series>(`${API}/series/${slug}`)
    } catch (err) {
        console.error('getSeries error:', err)
        return null
    }
}

export async function getTrending(): Promise<Movie[]> {
    try {
        return await fetchJSON<Movie[]>(`${API}/trending`) ?? []
    } catch (err) {
        console.error('getTrending error:', err)
        return []
    }
}

export async function getMovie(slug: string): Promise<Movie | null> {
    try {
        if (!slug) return null
        return await fetchJSON<Movie>(`${API}/movies/${slug}`)
    } catch (err) {
        console.error('getMovie error:', err)
        return null
    }
}

export async function searchMovies(q: string): Promise<Movie[]> {
    try {
        if (!q.trim()) return []
        return await fetchJSON<Movie[]>(`${API}/search?q=${encodeURIComponent(q)}`) ?? []
    } catch (err) {
        console.error('searchMovies error:', err)
        return []
    }
}