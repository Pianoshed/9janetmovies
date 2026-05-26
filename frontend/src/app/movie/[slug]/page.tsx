import { getMovie, getTrending, getAllSeries } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import { notFound } from 'next/navigation'

interface Props {
    params: Promise<{ slug: string }>
}

export default async function MoviePage({ params }: Props) {
    const { slug } = await params

    const [movie, trending, series] = await Promise.all([
        getMovie(slug),
        getTrending(),
        getAllSeries(),
    ])

    if (!movie || !movie.title) return notFound()

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

                    <SectionHeading>🎬 {movie.title}</SectionHeading>

                    {/* MOVIE INFO CARD */}
                    <div style={{
                        background: 'var(--white)',
                        border: '1px solid var(--border)',
                        borderRadius: '4px',
                        padding: '16px',
                        marginBottom: '16px',
                    }}>
                        <div className="movie-info-inner">

                            {/* POSTER */}
                            <div className="movie-poster">
                                {movie.poster_url ? (
                                    <img
                                        src={movie.poster_url}
                                        alt={movie.title}
                                        style={{
                                            width: '100%',
                                            borderRadius: '4px',
                                            objectFit: 'cover',
                                            display: 'block',
                                        }}
                                    />
                                ) : (
                                    <div style={{
                                        width: '100%',
                                        aspectRatio: '2/3',
                                        background: '#dce3f5',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '60px',
                                        borderRadius: '4px',
                                    }}>
                                        🎬
                                    </div>
                                )}
                            </div>

                            {/* DETAILS */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <h1 style={{
                                    fontSize: 'clamp(16px, 4vw, 22px)',
                                    fontWeight: 700,
                                    marginBottom: '12px',
                                    color: 'var(--blue-dark)',
                                    lineHeight: 1.3,
                                }}>
                                    {movie.title}
                                </h1>

                                {/* BADGES */}
                                <div style={{ marginBottom: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                    {movie.badge && (
                                        <span style={{
                                            background: 'var(--red)',
                                            color: 'var(--white)',
                                            fontSize: '11px',
                                            padding: '3px 8px',
                                            borderRadius: '2px',
                                            fontWeight: 600,
                                            textTransform: 'uppercase',
                                        }}>
                                            {movie.badge}
                                        </span>
                                    )}
                                    {movie.genre && (
                                        <span style={{
                                            background: 'var(--blue-light)',
                                            color: 'var(--blue)',
                                            fontSize: '11px',
                                            padding: '3px 8px',
                                            borderRadius: '2px',
                                            border: '1px solid #aac0ff',
                                        }}>
                                            {movie.genre}
                                        </span>
                                    )}
                                </div>

                                {movie.year && (
                                    <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '8px' }}>
                                        📅 Year: <strong>{movie.year}</strong>
                                    </p>
                                )}

                                {movie.description && (
                                    <p style={{
                                        fontSize: '14px',
                                        lineHeight: 1.7,
                                        color: '#333',
                                        marginTop: '12px',
                                        borderTop: '1px solid var(--border)',
                                        paddingTop: '12px',
                                    }}>
                                        {movie.description}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* DOWNLOAD LINKS */}
                    <SectionHeading>⬇️ Download Links</SectionHeading>
                    <div style={{
                        background: 'var(--white)',
                        border: '1px solid var(--border)',
                        borderRadius: '4px',
                        padding: '16px',
                        marginBottom: '16px',
                    }}>
                        {movie.links && movie.links.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                {movie.links.map((link, i) => (
                                    <a
                                        key={i}
                                        href={link.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: '8px',
                                            padding: '14px 20px',
                                            background: 'var(--blue-dark)',
                                            color: 'var(--white)',
                                            borderRadius: '4px',
                                            fontSize: '15px',
                                            fontWeight: 600,
                                            textDecoration: 'none',
                                            border: '2px solid var(--blue)',
                                            textAlign: 'center',
                                            width: '100%',
                                            boxSizing: 'border-box',
                                        }}
                                    >
                                        ⬇️ {link.label} — {link.host}
                                    </a>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: 'var(--muted)', fontSize: '14px' }}>
                                No download links available yet.
                            </p>
                        )}
                    </div>

                    {/* DISCLAIMER */}
                    <div style={{
                        background: '#fff9e6',
                        border: '1px solid #ffe082',
                        borderRadius: '4px',
                        padding: '12px 16px',
                        fontSize: '13px',
                        color: '#666',
                        lineHeight: 1.6,
                    }}>
                        ⚠️ 9janetmovies does not host any files. All download links point to third-party file hosting services.
                    </div>

                </main>

                <div className="sidebar-wrapper">
                    <Sidebar trending={trending} series={series} />
                </div>
            </div>

            <style>{`
                .movie-info-inner {
                    display: flex;
                    gap: 20px;
                    align-items: flex-start;
                }
                .movie-poster {
                    width: 180px;
                    flex-shrink: 0;
                }
                .sidebar-wrapper {
                    width: 260px;
                    flex-shrink: 0;
                }

                @media (max-width: 700px) {
                    .sidebar-wrapper {
                        display: none;
                    }
                }

                @media (max-width: 520px) {
                    .movie-info-inner {
                        flex-direction: column;
                    }
                    .movie-poster {
                        width: 100%;
                        max-width: 200px;
                        margin: 0 auto;
                    }
                }
            `}</style>
        </>
    )
}