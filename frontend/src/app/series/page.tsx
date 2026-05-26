import { getAllSeries, getTrending } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import SectionHeading from '@/components/ui/SectionHeading'
import Link from 'next/link'

export default async function SeriesPage({
    searchParams,
}: {
    searchParams: Promise<{ page?: string }>
}) {
    const { page: pageParam } = await searchParams
    const PAGE_SIZE = 24
    const page = Math.max(1, parseInt(pageParam || '1', 10))

    const [allSeries, trending] = await Promise.all([
        getAllSeries(),
        getTrending(),
    ])

    const totalPages = Math.ceil(allSeries.length / PAGE_SIZE)
    const series = allSeries.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

    return (
        <>
            <div style={{
                maxWidth: '1100px',
                margin: '16px auto',
                padding: '0 10px',
                display: 'flex',
                gap: '16px',
                alignItems: 'flex-start'
            }}>
                <main style={{ flex: '1 1 0', minWidth: 0 }}>
                    <SectionHeading>📺 All Series</SectionHeading>

                    {series.length === 0 && (
                        <div style={{
                            padding: '40px',
                            textAlign: 'center',
                            background: 'var(--white)',
                            border: '1px solid var(--border)',
                            color: 'var(--muted)'
                        }}>
                            No series added yet.
                        </div>
                    )}

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                        gap: '12px'
                    }}>
                        {series.map(s => (
                            <div key={s.id} style={{
                                background: 'var(--white)',
                                border: '1px solid var(--border)',
                                borderRadius: '4px',
                                overflow: 'hidden'
                            }}>
                                <Link href={`/series/${s.slug}`} style={{ display: 'block' }}>
                                    {s.poster_url ? (
                                        <img
                                            src={s.poster_url}
                                            alt={s.title}
                                            loading="lazy"
                                            style={{
                                                width: '100%',
                                                aspectRatio: '2/3',
                                                objectFit: 'cover',
                                                display: 'block'
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
                                            fontSize: '40px',
                                            color: '#aac0ff'
                                        }}>
                                            🎬
                                        </div>
                                    )}
                                    <div style={{ padding: '8px' }}>
                                        <div style={{
                                            fontSize: '13px',
                                            fontWeight: 600,
                                            lineHeight: 1.4,
                                            display: '-webkit-box',
                                            WebkitLineClamp: 2,
                                            WebkitBoxOrient: 'vertical',
                                            overflow: 'hidden',
                                        }}>
                                            {s.title}
                                        </div>
                                        <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
                                            {s.genre}
                                        </div>
                                    </div>
                                </Link>
                            </div>
                        ))}
                    </div>

                    {/* PAGINATION */}
                    {totalPages > 1 && (
                        <div className="pagination">
                            {/* Prev */}
                            {page > 1 ? (
                                <Link href={`/series?page=${page - 1}`} className="page-btn">
                                    ← Prev
                                </Link>
                            ) : (
                                <span className="page-btn disabled">← Prev</span>
                            )}

                            {/* Page numbers */}
                            {Array.from({ length: totalPages }, (_, i) => i + 1)
                                .filter(p =>
                                    p === 1 ||
                                    p === totalPages ||
                                    Math.abs(p - page) <= 1
                                )
                                .reduce<(number | '...')[]>((acc, p, i, arr) => {
                                    if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push('...')
                                    acc.push(p)
                                    return acc
                                }, [])
                                .map((p, i) =>
                                    p === '...' ? (
                                        <span key={`dots-${i}`} className="page-dots">…</span>
                                    ) : (
                                        <Link
                                            key={p}
                                            href={`/series?page=${p}`}
                                            className={`page-btn${p === page ? ' active' : ''}`}
                                        >
                                            {p}
                                        </Link>
                                    )
                                )
                            }

                            {/* Next */}
                            {page < totalPages ? (
                                <Link href={`/series?page=${page + 1}`} className="page-btn">
                                    Next →
                                </Link>
                            ) : (
                                <span className="page-btn disabled">Next →</span>
                            )}
                        </div>
                    )}
                </main>

                <div className="sidebar-wrapper">
                    <Sidebar trending={trending} series={allSeries} />
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

                .pagination {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 6px;
                    margin-top: 24px;
                    padding-bottom: 8px;
                }
                .page-btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 36px;
                    height: 36px;
                    padding: 0 10px;
                    border: 1px solid var(--border);
                    border-radius: 4px;
                    background: var(--white);
                    color: var(--black);
                    font-size: 13px;
                    font-weight: 500;
                    text-decoration: none;
                    cursor: pointer;
                    transition: background 0.1s;
                }
                .page-btn:hover:not(.disabled):not(.active) {
                    background: var(--grey);
                }
                .page-btn.active {
                    background: var(--blue-dark);
                    color: var(--white);
                    border-color: var(--blue-dark);
                    font-weight: 700;
                }
                .page-btn.disabled {
                    color: var(--muted);
                    cursor: default;
                    opacity: 0.5;
                }
                .page-dots {
                    font-size: 13px;
                    color: var(--muted);
                    padding: 0 4px;
                }
            `}</style>
        </>
    )
}