'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Movie } from '@/lib/types'
import { DownloadLinks } from '@/components/movie/DownloadLinks'
import { SubtitleSearch } from '@/components/movie/SubtitleSearch'

interface Props {
    movie: Movie
}

export function MovieHero({ movie }: Props) {
    const [showSubtitles, setShowSubtitles] = useState(false)

    return (
        <section className="movie-hero">
            {/* Poster */}
            <div className="movie-hero__poster">
                {movie.poster_url ? (
                    <Image
                        src={movie.poster_url}
                        alt={movie.title}
                        width={300}
                        height={450}
                        className="movie-hero__img"
                        priority
                    />
                ) : (
                    <div className="movie-hero__no-poster">No Image</div>
                )}
            </div>

            {/* Info */}
            <div className="movie-hero__info">
                <div className="movie-hero__meta">
                    {movie.badge && <span className="badge">{movie.badge}</span>}
                    {movie.is_trending && <span className="badge badge--trending">Trending</span>}
                    <span className="movie-hero__genre">{movie.genre}</span>
                    <span className="movie-hero__year">{movie.year}</span>
                </div>

                <h1 className="movie-hero__title">{movie.title}</h1>

                {movie.description && (
                    <p className="movie-hero__description">{movie.description}</p>
                )}

                {/* Download Links */}
                <div className="movie-hero__downloads">
                    <h3 className="movie-hero__section-label">Download</h3>
                    <DownloadLinks links={movie.links} />
                </div>

                {/* Subtitle */}
                <div className="movie-hero__subtitles">
                    <button
                        onClick={() => setShowSubtitles((prev) => !prev)}
                        className="subtitle-btn"
                    >
                        📄 {showSubtitles ? 'Hide Subtitles' : 'Download Subtitle'}
                    </button>

                    {showSubtitles && (
                        <SubtitleSearch movieTitle={movie.title} />
                    )}
                </div>
            </div>
        </section>
    )
}