// app/series/[slug]/page.tsx
import { getSeries, getTrending, getAllSeries } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import { notFound } from 'next/navigation'

interface Props {
    params: Promise<{ slug: string }>
}

export default async function SeriesPage({ params }: Props) {
    const { slug } = await params

    const [series, trending, allSeries] = await Promise.all([
        getSeries(slug),
        getTrending(),
        getAllSeries(),
    ])

    if (!series || !series.title) return notFound()

    // Group episodes by season
    const seasons: Record<number, typeof series.episodes> = {}
    for (const ep of series.episodes || []) {
        if (!seasons[ep.season]) seasons[ep.season] = []
        seasons[ep.season].push(ep)
    }
    const seasonNumbers = Object.keys(seasons).map(Number).sort((a, b) => a - b)

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

                    <SectionHeading>🎬 {series.title}</SectionHeading>

                    {/* SERIES INFO */}
                    <div style={{
                        background: 'var(--white)',
                        border: '1px solid var(--border)',
                        borderRadius: '4px',
                        padding: '16px',
                        marginBottom: '16px',
                    }}>
                        <div className="series-info-inner">

                            {/* POSTER */}
                            <div className="series-poster">
                                {series.poster_url ? (
                                    <img
                                        src={series.poster_url}
                                        alt={series.title}
                                        style={{ width: '100%', borderRadius: '4px', objectFit: 'cover' }}
                                    />
                                ) : (
                                    <div style={{
                                        width: '100%',
                                        aspectRatio: '2/3',
                                        background: '#dce3f5',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '50px',
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
                                    {series.title}
                                </h1>

                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
                                    {series.genre && (
                                        <span style={{
                                            background: 'var(--blue-light)',
                                            color: 'var(--blue)',
                                            fontSize: '11px',
                                            padding: '3px 8px',
                                            borderRadius: '2px',
                                            border: '1px solid #aac0ff',
                                        }}>
                                            {series.genre}
                                        </span>
                                    )}
                                    <span style={{
                                        background: 'var(--grey)',
                                        color: 'var(--muted)',
                                        fontSize: '11px',
                                        padding: '3px 8px',
                                        borderRadius: '2px',
                                        border: '1px solid var(--border)',
                                    }}>
                                        {seasonNumbers.length} Season{seasonNumbers.length !== 1 ? 's' : ''}
                                    </span>
                                </div>

                                {series.description && (
                                    <p style={{
                                        fontSize: '14px',
                                        lineHeight: 1.7,
                                        color: '#333',
                                        borderTop: '1px solid var(--border)',
                                        paddingTop: '12px',
                                        marginTop: '8px',
                                    }}>
                                        {series.description}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* EPISODES BY SEASON */}
                    {seasonNumbers.length === 0 ? (
                        <div style={{
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            borderRadius: '4px',
                            padding: '20px',
                            textAlign: 'center',
                            color: 'var(--muted)',
                            fontSize: '14px',
                        }}>
                            No episodes available yet.
                        </div>
                    ) : (
                        seasonNumbers.map(seasonNum => (
                            <div key={seasonNum} style={{ marginBottom: '16px' }}>
                                <SectionHeading>
                                    {seasonNum === 0 ? '📦 Season Packs' : `📺 Season ${seasonNum}`}
                                </SectionHeading>
                                <div style={{
                                    background: 'var(--white)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '4px',
                                    overflow: 'hidden',
                                }}>
                                    {seasons[seasonNum]
                                        .sort((a, b) => a.episode - b.episode)
                                        .map((ep, i) => (
                                            <a
                                                key={i}
                                                href={ep.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="episode-row"
                                                style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'space-between',
                                                    padding: '12px 16px',
                                                    borderBottom: '1px solid var(--border)',
                                                    gap: '12px',
                                                    textDecoration: 'none',
                                                    color: 'var(--black)',
                                                }}
                                            >
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <div style={{
                                                        fontSize: '13px',
                                                        fontWeight: 600,
                                                        marginBottom: '2px',
                                                        overflow: 'hidden',
                                                        textOverflow: 'ellipsis',
                                                        whiteSpace: 'nowrap',
                                                    }}>
                                                        {ep.episode === 0
                                                            ? `📦 Full Season ${seasonNum} Pack`
                                                            : `Ep ${ep.episode} — ${ep.title || `Episode ${ep.episode}`}`
                                                        }
                                                    </div>
                                                    <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                                                        {ep.host}
                                                    </div>
                                                </div>
                                                <div style={{
                                                    background: 'var(--blue-dark)',
                                                    color: 'var(--white)',
                                                    fontSize: '12px',
                                                    fontWeight: 600,
                                                    padding: '6px 14px',
                                                    borderRadius: '3px',
                                                    whiteSpace: 'nowrap',
                                                    flexShrink: 0,
                                                }}>
                                                    ⬇️ Download
                                                </div>
                                            </a>
                                        ))
                                    }
                                </div>
                            </div>
                        ))
                    )}

                    {/* DISCLAIMER */}
                    <div style={{
                        background: '#fff9e6',
                        border: '1px solid #ffe082',
                        borderRadius: '4px',
                        padding: '12px 16px',
                        fontSize: '13px',
                        color: '#666',
                        lineHeight: 1.6,
                        marginTop: '8px',
                    }}>
                        ⚠️ 9janetmovies does not host any files. All download links point to third-party hosting services.
                    </div>

                </main>

                <div className="sidebar-wrapper">
                    <Sidebar trending={trending} series={allSeries} />
                </div>
            </div>

            <style>{`
                .series-info-inner {
                    display: flex;
                    gap: 20px;
                    align-items: flex-start;
                }
                .series-poster {
                    width: 180px;
                    flex-shrink: 0;
                }
                .sidebar-wrapper {
                    width: 260px;
                    flex-shrink: 0;
                }
                .episode-row:hover {
                    background: var(--grey);
                }
                .episode-row:last-child {
                    border-bottom: none;
                }
                @media (max-width: 700px) {
                    .sidebar-wrapper { display: none; }
                }
                @media (max-width: 520px) {
                    .series-info-inner { flex-direction: column; }
                    .series-poster {
                        width: 100%;
                        max-width: 200px;
                        margin: 0 auto;
                    }
                }
            `}</style>
        </>
    )
}