export const dynamic = 'force-dynamic'
import { Suspense } from 'react'
import { getMovies, getTrending, getAllSeries } from '@/lib/api'
import MovieGrid from '@/components/movies/MovieGrid'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import FilterBar from '@/components/movies/FilterBar'
import Pagination from '@/components/movies/Pagination'

interface Props {
    params: Promise<{ genre: string }>
    searchParams: Promise<{ page?: string }>
}

export default async function GenrePage({ params, searchParams }: Props) {
    const { genre } = await params
    const { page: pageParam } = await searchParams
    const page = parseInt(pageParam || '1', 10)

    const genreLabel = genre.charAt(0).toUpperCase() + genre.slice(1)

    const [data, trending, series] = await Promise.all([
        getMovies(page, genre),
        getTrending(),
        getAllSeries(),
    ])

    return (
        <>
            <div style={{
                maxWidth: '1100px',
                margin: '16px auto',
                padding: '0 12px',
                display: 'flex',
                gap: '16px',
                alignItems: 'flex-start',
            }}>
                <main style={{ flex: '1 1 0', minWidth: 0 }}>
                    <SectionHeading>🎬 {genreLabel} Movies</SectionHeading>

                    <Suspense fallback={<div>Loading filters...</div>}>
                        <FilterBar />
                    </Suspense>

                    {data.movies.length === 0 ? (
                        <div style={{
                            padding: '40px',
                            textAlign: 'center',
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            borderRadius: '4px',
                            color: 'var(--muted)',
                            marginTop: '16px'
                        }}>
                            No {genreLabel} movies found.
                        </div>
                    ) : (
                        <MovieGrid movies={data.movies} />
                    )}

                    <Pagination current={page} total={data.pages} basePath={`tag/${genre}`} />
                </main>

                <div className="sidebar-wrapper">
                    <Sidebar trending={trending} series={series} />
                </div>
            </div>

            <style>{`
                .sidebar-wrapper {
                    width: 260px;
                    flex-shrink: 0;
                }
                @media (max-width: 700px) {
                    .sidebar-wrapper {
                        display: none;
                    }
                }
            `}</style>
        </>
    )
}