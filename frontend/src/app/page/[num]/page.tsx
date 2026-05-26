export const dynamic = 'force-dynamic';
import { Suspense } from 'react'
import { getMovies, getTrending, getAllSeries } from '@/lib/api'
import MovieGrid from '@/components/movies/MovieGrid'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import Pagination from '@/components/movies/Pagination'
import FilterBar from '@/components/movies/FilterBar'
import { redirect } from 'next/navigation'

interface Props {
    params: Promise<{ num: string }>
}

export default async function PageNum({ params }: Props) {
    const { num } = await params
    const page = parseInt(num) || 1

    if (page === 1) redirect('/')

    const [data, trending, series] = await Promise.all([
        getMovies(page),
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
                    <SectionHeading>⚡ Latest Movies</SectionHeading>
                    <Suspense fallback={<div>Loading filters...</div>}>
                        <FilterBar />
                    </Suspense>
                    <MovieGrid movies={data.movies} />
                    <Pagination current={page} total={data.pages} basePath="page" />
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