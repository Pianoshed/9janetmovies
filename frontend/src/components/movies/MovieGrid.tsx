import { Movie } from '@/lib/types'
import MovieCard from './MovieCard'

interface Props {
    movies: Movie[]
}

export default function MovieGrid({ movies }: Props) {
    if (movies.length === 0) {
        return (
            <div style={{
                textAlign: 'center',
                padding: '40px 20px',
                color: 'var(--muted)',
                background: 'var(--white)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                marginBottom: '16px',
                fontSize: '15px',
            }}>
                No movies found.
            </div>
        )
    }

    return (
        <>
            <div className="movie-grid">
                {movies.map(movie => (
                    <MovieCard key={movie.id} movie={movie} />
                ))}
            </div>

            <style>{`
        .movie-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }

        /* Mobile: 2 columns */
        @media (max-width: 480px) {
          .movie-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
          }
        }

        /* Small mobile: still 2 but tighter */
        @media (max-width: 360px) {
          .movie-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
          }
        }
      `}</style>
        </>
    )
}