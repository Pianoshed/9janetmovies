import Link from 'next/link'
import { Movie } from '@/lib/types'

interface Props {
    movie: Movie
}

export default function MovieCard({ movie }: Props) {
    return (
        <div style={{
            background: 'var(--white)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            overflow: 'hidden',
        }}>
            <Link href={`/movie/${movie.slug}`} style={{ display: 'block' }}>

                {/* POSTER */}
                {movie.poster_url ? (
                    <img
                        src={movie.poster_url}
                        alt={movie.title}
                        style={{ width: '100%', aspectRatio: '2/3', objectFit: 'cover' }}
                    />
                ) : (
                    <div style={{
                        width: '100%',
                        aspectRatio: '2/3',
                        background: '#dce3f5',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '40px',
                        color: '#aac0ff',
                        minHeight: '180px'
                    }}>
                        🎬
                    </div>
                )}

                {/* BODY */}
                <div style={{ padding: '8px' }}>
                    {movie.badge && (
                        <div style={{
                            display: 'inline-block',
                            background: 'var(--red)',
                            color: 'var(--white)',
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '2px',
                            marginBottom: '4px',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}>
                            {movie.badge}
                        </div>
                    )}
                    <div style={{
                        fontSize: '13px',
                        fontWeight: 600,
                        lineHeight: 1.4,
                        color: 'var(--black)',
                        marginBottom: '4px',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                    }}>
                        {movie.title} {movie.year ? `(${movie.year})` : ''}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                        {movie.genre} &bull; {movie.year}
                    </div>
                </div>

            </Link>
        </div>
    )
}