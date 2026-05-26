import { searchMovies, getTrending, getAllSeries } from '@/lib/api'
import MovieGrid from '@/components/movies/MovieGrid'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'

interface Props {
    searchParams: Promise<{ q?: string }>
}

export default async function SearchPage({ searchParams }: Props) {
    const { q = '' } = await searchParams

    const [movies, trending, series] = await Promise.all([
        searchMovies(q),
        getTrending(),
        getAllSeries(),
    ])

    return (
        <div style={{
            maxWidth: '1100px',
            margin: '16px auto',
            padding: '0 10px',
            display: 'flex',
            gap: '16px',
            alignItems: 'flex-start'
        }}>
            <main style={{ flex: '1 1 0', minWidth: 0 }}>
                <SectionHeading>
                    🔍 Search results for: {q}
                </SectionHeading>
                <MovieGrid movies={movies} />
            </main>
            <Sidebar trending={trending} series={series} />
        </div>
    )
}