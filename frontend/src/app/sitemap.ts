import { MetadataRoute } from 'next'

const BASE_URL = 'https://9janetmovies.com.ng'
const API = process.env.NEXT_PUBLIC_API_URL || 'https://ninejamoviesnet.onrender.com/api'

const GENRES = [
    'action', 'thriller', 'horror', 'drama',
    'sci-fi', 'animation', 'korean', 'romance', 'crime', 'nollywood'
]

async function getMovieSlugs(): Promise<string[]> {
    try {
        const slugs: string[] = []
        let page = 1
        while (true) {
            const res = await fetch(`${API}/movies?page=${page}`, { cache: 'no-store' })
            if (!res.ok) break
            const data = await res.json()
            if (!data.movies || data.movies.length === 0) break
            slugs.push(...data.movies.map((m: any) => m.slug))
            if (page >= data.pages) break
            page++
        }
        return slugs
    } catch {
        return []
    }
}

async function getSeriesSlugs(): Promise<string[]> {
    try {
        const res = await fetch(`${API}/series`, { cache: 'no-store' })
        if (!res.ok) return []
        const data = await res.json()
        return data.map((s: any) => s.slug)
    } catch {
        return []
    }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    const [movieSlugs, seriesSlugs] = await Promise.all([
        getMovieSlugs(),
        getSeriesSlugs(),
    ])

    const staticPages: MetadataRoute.Sitemap = [
        { url: BASE_URL, priority: 1.0, changeFrequency: 'daily' },
        { url: `${BASE_URL}/series`, priority: 0.9, changeFrequency: 'daily' },
        { url: `${BASE_URL}/search`, priority: 0.7, changeFrequency: 'weekly' },
        { url: `${BASE_URL}/contact`, priority: 0.5, changeFrequency: 'monthly' },
        { url: `${BASE_URL}/privacy-policy`, priority: 0.3, changeFrequency: 'monthly' },
        { url: `${BASE_URL}/disclaimer`, priority: 0.3, changeFrequency: 'monthly' },
        { url: `${BASE_URL}/dmca`, priority: 0.3, changeFrequency: 'monthly' },
    ]

    const genrePages: MetadataRoute.Sitemap = GENRES.map(genre => ({
        url: `${BASE_URL}/tag/${genre}`,
        priority: 0.8,
        changeFrequency: 'daily' as const,
    }))

    const moviePages: MetadataRoute.Sitemap = movieSlugs.map(slug => ({
        url: `${BASE_URL}/movie/${slug}`,
        priority: 0.7,
        changeFrequency: 'weekly' as const,
    }))

    const seriesPages: MetadataRoute.Sitemap = seriesSlugs.map(slug => ({
        url: `${BASE_URL}/series/${slug}`,
        priority: 0.7,
        changeFrequency: 'weekly' as const,
    }))

    return [...staticPages, ...genrePages, ...moviePages, ...seriesPages]
}