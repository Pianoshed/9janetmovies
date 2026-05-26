import { getMovies, getTrending, getAllSeries } from '@/lib/api'
import MovieGrid from '@/components/movies/MovieGrid'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import Pagination from '@/components/movies/Pagination'
import FilterBar from '@/components/movies/FilterBar'

export default async function Home() {
  const [data, trending, series] = await Promise.all([
    getMovies(1),
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
          <FilterBar />
          <MovieGrid movies={data.movies} />
          <Pagination current={1} total={data.pages} basePath="page" />
        </main>

        {/* Sidebar hidden on mobile via CSS */}
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