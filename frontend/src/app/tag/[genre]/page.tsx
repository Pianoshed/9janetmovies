import { getMovies } from '@/lib/api'
import MovieGrid from '@/components/movies/MovieGrid'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import Pagination from '@/components/movies/Pagination'
import { getTrending, getAllSeries } from '@/lib/api'

interface Props {
    params: Promise<{ genre: string }>
}

export default async function GenrePage({ params }: Props) {
    const { genre } = await params

    const [data, trending, series] = await Promise.all([
        getMovies(1, genre),
        getTrending(),
        getAllSeries(),
    ])

    const genreLabel = genre.charAt(0).toUpperCase() + genre.slice(1)

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
                <SectionHeading>⚡ {genreLabel} Movies</SectionHeading>
                <MovieGrid movies={data.movies} />
                <Pagination
                    current={data.current}
                    total={data.pages}
                    basePath={`/tag/${genre}`}
                />
            </main>
            <Sidebar trending={trending} series={series} />
        </div>
    )
}