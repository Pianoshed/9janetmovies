import Link from 'next/link'
import { Movie, Series } from '@/lib/types'
import WidgetTitle from '@/components/ui/WidgetTitle'
import TagCloud from '@/components/ui/TagCloud'

interface Props {
    trending: Movie[]
    series: Series[]
}

export default function Sidebar({ trending, series }: Props) {
    return (
        <aside style={{
            width: '260px',
            flexShrink: 0,
            position: 'sticky',
            top: '10px',
        }}>

            {/* TRENDING */}
            <div style={{ marginBottom: '16px' }}>
                <WidgetTitle>Trending</WidgetTitle>
                <ul style={{ listStyle: 'none' }}>
                    {trending.length === 0 && (
                        <li style={{
                            padding: '10px',
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            fontSize: '13px',
                            color: 'var(--muted)',
                        }}>
                            No trending movies yet.
                        </li>
                    )}
                    {trending.map(movie => (
                        <li key={movie.id} style={{
                            display: 'flex',
                            alignItems: 'center',
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            marginBottom: '4px',
                            borderRadius: '2px',
                            overflow: 'hidden',
                        }}>
                            <div style={{
                                width: '52px', height: '66px',
                                background: '#dce3f5', flexShrink: 0,
                                display: 'flex', alignItems: 'center',
                                justifyContent: 'center', fontSize: '20px',
                            }}>
                                {movie.poster_url
                                    ? <img src={movie.poster_url} alt={movie.title} loading="lazy" style={{ width: '52px', height: '66px', objectFit: 'cover' }} />
                                    : '🎬'
                                }
                            </div>
                            <div style={{ padding: '6px 8px', fontSize: '12px', fontWeight: 600, lineHeight: 1.4 }}>
                                <Link href={`/movie/${movie.slug}`}>{movie.title}</Link>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {/* SERIES */}
            <div style={{ marginBottom: '16px' }}>
                <WidgetTitle href="/series">Series</WidgetTitle>
                <ul style={{ listStyle: 'none' }}>
                    {series.length === 0 && (
                        <li style={{
                            padding: '10px',
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            fontSize: '13px',
                            color: 'var(--muted)',
                        }}>
                            No series yet.
                        </li>
                    )}
                    {series.slice(0, 3).map(s => (
                        <li key={s.id} style={{
                            display: 'flex', alignItems: 'center',
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            marginBottom: '4px', borderRadius: '2px',
                            overflow: 'hidden', padding: '6px', gap: '8px',
                        }}>
                            {/* FIX: was hardcoded 🎬, now renders poster_url */}
                            <div style={{
                                width: '48px', height: '60px', background: '#dce3f5',
                                flexShrink: 0, display: 'flex', alignItems: 'center',
                                justifyContent: 'center', fontSize: '18px',
                                borderRadius: '2px', overflow: 'hidden',
                            }}>
                                {s.poster_url
                                    ? <img
                                        src={s.poster_url}
                                        alt={s.title}
                                        loading="lazy"
                                        style={{ width: '48px', height: '60px', objectFit: 'cover' }}
                                    />
                                    : '🎬'
                                }
                            </div>
                            <div>
                                <div style={{ fontSize: '12px', fontWeight: 600, lineHeight: 1.4 }}>
                                    <Link href={`/series/${s.slug}`}>{s.title}</Link>
                                </div>
                                <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>
                                    {new Date(s.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {/* GENRES */}
            <div style={{ marginBottom: '16px' }}>
                <WidgetTitle>Genres</WidgetTitle>
                <TagCloud />
            </div>

        </aside>
    )
}