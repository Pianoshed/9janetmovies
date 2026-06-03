'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useState } from 'react'
import { Movie } from '@/lib/types'

interface Props {
    movie: Movie
}

export default function MovieCard({ movie }: Props) {
    const [imgError, setImgError] = useState(false)

    return (
        <div
            style={{
                background: 'var(--white)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                overflow: 'hidden',
                transition: 'box-shadow 0.15s ease',
            }}
            className="movie-card"
        >
            <Link href={`/movie/${movie.slug}`} style={{ display: 'block' }}>

                {/* POSTER */}
                <div style={{ position: 'relative', width: '100%', aspectRatio: '2/3' }}>
                    {movie.poster_url && !imgError ? (
                        <Image
                            src={movie.poster_url}
                            alt={movie.title}
                            fill
                            sizes="(max-width: 360px) 45vw, (max-width: 480px) 45vw, (max-width: 700px) 30vw, 160px"
                            style={{ objectFit: 'cover' }}
                            loading="lazy"
                            onError={() => setImgError(true)}
                        />
                    ) : (
                        <div style={{
                            width: '100%',
                            height: '100%',
                            background: '#dce3f5',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '36px',
                            color: '#aac0ff',
                        }}>
                            🎬
                        </div>
                    )}
                </div>

                {/* BODY */}
                <div style={{ padding: '7px 8px 9px' }}>
                    {movie.badge && (
                        <div style={{
                            display: 'inline-block',
                            background: 'var(--red)',
                            color: 'var(--white)',
                            fontSize: '9px',
                            padding: '2px 5px',
                            borderRadius: '2px',
                            marginBottom: '4px',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                        }}>
                            {movie.badge}
                        </div>
                    )}
                    <div style={{
                        fontSize: '12px',
                        fontWeight: 600,
                        lineHeight: 1.4,
                        color: 'var(--black)',
                        marginBottom: '3px',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                    }}>
                        {movie.title}{movie.year ? ` (${movie.year})` : ''}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--muted)' }}>
                        {movie.genre}{movie.year ? ` · ${movie.year}` : ''}
                    </div>
                </div>

            </Link>

            <style>{`
                .movie-card:hover {
                    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
                }
                @media (max-width: 480px) {
                    .movie-card a div[style*="padding"] {
                        padding: 6px 7px 8px;
                    }
                }
            `}</style>
        </div>
    )
}