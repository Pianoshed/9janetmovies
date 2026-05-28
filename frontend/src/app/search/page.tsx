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
        <>
            <div style={{
                maxWidth: '1100px',
                margin: '16px auto',
                padding: '0 10px',
                display: 'flex',
                gap: '16px',
                alignItems: 'flex-start',
            }}>
                <main style={{ flex: '1 1 0', minWidth: 0 }}>
                    <SectionHeading>
                        🔍 Search results for: <em>{q}</em>
                    </SectionHeading>

                    {movies.length === 0 ? (
                        <div style={{
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            borderRadius: '4px',
                            padding: '32px 16px',
                            textAlign: 'center',
                            color: 'var(--muted)',
                            fontSize: '15px',
                        }}>
                            No results found for <strong>{q}</strong>. Try a different search.
                        </div>
                    ) : (
                        <MovieGrid movies={movies} />
                    )}
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
                    .sidebar-wrapper { display: none; }
                }
            `}</style>
        </>
    )
}