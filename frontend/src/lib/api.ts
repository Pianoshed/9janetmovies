import { Movie, MoviesResponse, Series } from './types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000/api'
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY

// Revalidation times (seconds)
const REVALIDATE = {
    movies:   300,  // 5 mins  — new movies added occasionally
    genre:    300,  // 5 mins  — matches Flask cache timeout
    trending: 180,  // 3 mins  — changes more frequently
    series:   600,  // 10 mins — rarely changes
    movie:    600,  // 10 mins — individual movie rarely changes
    search:     0,  // no cache — must be fresh
}

async function fetchJSON<T>(url: string, revalidate: number): Promise<T | null> {
    const res = await fetch(url, {
        next: revalidate === 0
            ? { revalidate: 0 }        // search: always fresh
            : { revalidate },          // everything else: ISR cache
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
        const data = await fetchJSON<any>(url, REVALIDATE.movies)
        return {
            movies:  data?.movies  ?? [],
            total:   data?.total   ?? 0,
            pages:   data?.pages   ?? 0,
            current: data?.current ?? page,
        }
    } catch (err) {
        console.error('getMovies error:', err)
        return { movies: [], total: 0, pages: 0, current: page }
    }
}

export async function getMoviesByGenre(genre: string, page = 1): Promise<MoviesResponse> {
    try {
        const url = `${API}/genres/${encodeURIComponent(genre)}?page=${page}`
        const data = await fetchJSON<any>(url, REVALIDATE.genre)
        return {
            movies:  data?.movies  ?? [],
            total:   data?.total   ?? 0,
            pages:   data?.pages   ?? 0,
            current: data?.current ?? page,
        }
    } catch (err) {
        console.error('getMoviesByGenre error:', err)
        return { movies: [], total: 0, pages: 0, current: page }
    }
}

export async function getAllSeries(): Promise<Series[]> {
    try {
        const data = await fetchJSON<any>(`${API}/series?slim=true`, REVALIDATE.series) ?? {}
        return data?.series ?? []
    } catch (err) {
        console.error('getAllSeries error:', err)
        return []
    }
}

export async function getSeries(slug: string): Promise<Series | null> {
    try {
        if (!slug) return null
        return await fetchJSON<Series>(`${API}/series/${slug}`, REVALIDATE.series)
    } catch (err) {
        console.error('getSeries error:', err)
        return null
    }
}

export async function getTrending(): Promise<Movie[]> {
    try {
        return await fetchJSON<Movie[]>(`${API}/trending`, REVALIDATE.trending) ?? []
    } catch (err) {
        console.error('getTrending error:', err)
        return []
    }
}

export async function getMovie(slug: string): Promise<Movie | null> {
    try {
        if (!slug) return null
        return await fetchJSON<Movie>(`${API}/movies/${slug}`, REVALIDATE.movie)
    } catch (err) {
        console.error('getMovie error:', err)
        return null
    }
}

export async function searchMovies(q: string): Promise<Movie[]> {
    try {
        if (!q.trim()) return []
        return await fetchJSON<Movie[]>(
            `${API}/search?q=${encodeURIComponent(q)}`,
            REVALIDATE.search
        ) ?? []
    } catch (err) {
        console.error('searchMovies error:', err)
        return []
    }
}