'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000/api'

interface BlogPost {
    id: number
    title: string
    slug: string
    summary: string
    image_url: string | null
    source_name: string
    category: string
    published_at: string
}

function timeAgo(dateStr: string) {
    const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
    if (diff < 60) return 'just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

const CATEGORY_COLORS: Record<string, string> = {
    'Upcoming Movies': '#1565c0',
    'Reviews': '#e53935',
    'TV & Streaming': '#6a1b9a',
    'Box Office': '#2e7d32',
}

const CATEGORIES = ['All', 'Upcoming Movies', 'Reviews', 'TV & Streaming', 'Box Office']

function btnStyle(active: boolean, disabled: boolean): React.CSSProperties {
    return {
        minWidth: '40px',
        minHeight: '40px',
        padding: '6px 14px',
        fontSize: '14px',
        fontWeight: active ? 700 : 500,
        border: `1px solid ${active ? 'var(--red)' : 'var(--border)'}`,
        background: active ? 'var(--red)' : 'transparent',
        color: disabled ? 'var(--muted)' : active ? '#fff' : 'var(--blue-dark)',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        touchAction: 'manipulation',
    }
}

export default function BlogPage() {
    const [posts, setPosts] = useState<BlogPost[]>([])
    const [page, setPage] = useState(1)
    const [pages, setPages] = useState(1)
    const [total, setTotal] = useState(0)
    const [category, setCategory] = useState('')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        setLoading(true)
        window.scrollTo({ top: 0, behavior: 'smooth' })
        const params = new URLSearchParams({ page: String(page), limit: '12' })
        if (category) params.append('category', category)

        fetch(`${API}/blog?${params}`)
            .then(r => r.json())
            .then(data => {
                setPosts(data.posts ?? [])
                setPages(data.pages ?? 1)
                setTotal(data.total ?? 0)
                setLoading(false)
            })
            .catch(() => setLoading(false))
    }, [page, category])

    const handleCategory = (cat: string) => {
        setCategory(cat === 'All' ? '' : cat)
        setPage(1)
    }

    const pageNumbers = Array.from({ length: pages }, (_, i) => i + 1)
        .filter(n => n === 1 || n === pages || Math.abs(n - page) <= 1)

    return (
        <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '16px 12px' }}>

            {/* Header */}
            <div style={{ marginBottom: '16px' }}>
                <Link href="/" style={{ fontSize: '13px', color: 'var(--red)', textDecoration: 'none' }}>
                    ← Back to Home
                </Link>
                <h1 style={{ fontSize: '20px', fontWeight: 700, margin: '8px 0 0', color: 'var(--blue-dark)' }}>
                    🗞️ Entertainment Gist
                </h1>
                {total > 0 && (
                    <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '4px 0 0' }}>
                        {total} posts · Page {page} of {pages}
                    </p>
                )}
            </div>

            {/* Category filters — horizontal scroll on mobile */}
            <div style={{
                display: 'flex',
                gap: '8px',
                overflowX: 'auto',
                marginBottom: '16px',
                paddingBottom: '4px',
                WebkitOverflowScrolling: 'touch' as any,
                scrollbarWidth: 'none' as any,
            }}>
                {CATEGORIES.map(cat => {
                    const active = (cat === 'All' && !category) || cat === category
                    return (
                        <button
                            key={cat}
                            onClick={() => handleCategory(cat)}
                            style={{
                                flexShrink: 0,
                                padding: '7px 14px',
                                fontSize: '12px',
                                fontWeight: active ? 700 : 500,
                                border: `1px solid ${active ? 'var(--red)' : 'var(--border)'}`,
                                background: active ? 'var(--red)' : 'transparent',
                                color: active ? '#fff' : 'var(--blue-dark)',
                                borderRadius: '20px',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                touchAction: 'manipulation',
                                minHeight: '36px',
                            }}
                        >
                            {cat}
                        </button>
                    )
                })}
            </div>

            {/* Posts grid */}
            {loading ? (
                <p style={{ color: 'var(--muted)', fontSize: '14px', padding: '24px 0' }}>Loading...</p>
            ) : posts.length === 0 ? (
                <p style={{ color: 'var(--muted)', fontSize: '14px', padding: '24px 0' }}>No posts found.</p>
            ) : (
                <div className="blog-full-grid">
                    {posts.map(post => (
                        <Link key={post.id} href={`/blog/${post.slug}`} className="blog-card">
                            {post.image_url && (
                                <div className="blog-card-img">
                                    <img
                                        src={post.image_url}
                                        alt={post.title}
                                        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                                        onError={e => {
                                            (e.target as HTMLImageElement).parentElement!.style.display = 'none'
                                        }}
                                    />
                                </div>
                            )}
                            <div className="blog-card-body">
                                <div style={{ display: 'flex', gap: '6px', marginBottom: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                                    <span style={{
                                        background: CATEGORY_COLORS[post.category] ?? '#555',
                                        color: '#fff', fontSize: '10px', fontWeight: 700,
                                        padding: '2px 6px', borderRadius: '2px', textTransform: 'uppercase',
                                        flexShrink: 0,
                                    }}>
                                        {post.category}
                                    </span>
                                    <span style={{ fontSize: '11px', color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {post.source_name}
                                    </span>
                                    <span style={{ fontSize: '11px', color: 'var(--muted)', marginLeft: 'auto', whiteSpace: 'nowrap' }}>
                                        {timeAgo(post.published_at)}
                                    </span>
                                </div>
                                <h3 className="blog-card-title">
                                    {post.title}
                                </h3>
                                <div style={{ marginTop: 'auto', paddingTop: '8px', fontSize: '12px', color: 'var(--red)', fontWeight: 600 }}>
                                    Read more →
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {pages > 1 && (
                <div className="pagination-bar">
                    <button
                        onClick={() => setPage(p => p - 1)}
                        disabled={page === 1}
                        style={btnStyle(false, page === 1)}
                    >
                        ← Prev
                    </button>

                    {/* Page numbers — hidden on mobile */}
                    <div className="page-numbers">
                        {pageNumbers.map((n, idx) => (
                            <span key={n} style={{ display: 'contents' }}>
                                {idx > 0 && pageNumbers[idx - 1] !== n - 1 && (
                                    <span style={{ color: 'var(--muted)', fontSize: '13px', padding: '0 2px' }}>…</span>
                                )}
                                <button onClick={() => setPage(n)} style={btnStyle(n === page, false)}>
                                    {n}
                                </button>
                            </span>
                        ))}
                    </div>

                    {/* Mobile: just show current page */}
                    <span className="page-indicator" style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: 500 }}>
                        {page} / {pages}
                    </span>

                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={page === pages}
                        style={btnStyle(false, page === pages)}
                    >
                        Next →
                    </button>
                </div>
            )}

            <style>{`
                /* Hide scrollbar on category strip */
                div::-webkit-scrollbar { display: none; }

                .blog-full-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 12px;
                }
                .blog-card {
                    display: flex;
                    flex-direction: column;
                    background: var(--white);
                    border: 1px solid var(--border);
                    border-radius: 4px;
                    overflow: hidden;
                    text-decoration: none;
                    color: inherit;
                    transition: box-shadow 0.15s;
                }
                .blog-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
                .blog-card-img {
                    width: 100%;
                    height: 140px;
                    overflow: hidden;
                    background: #eee;
                    flex-shrink: 0;
                }
                .blog-card-body {
                    padding: 10px;
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                .blog-card-title {
                    font-size: 13px;
                    font-weight: 600;
                    line-height: 1.4;
                    color: var(--blue-dark);
                    margin: 0 0 6px;
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }
                .pagination-bar {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    margin-top: 28px;
                    flex-wrap: wrap;
                }
                .page-numbers { display: flex; align-items: center; gap: 6px; }
                .page-indicator { display: none; }

                @media (max-width: 1024px) {
                    .blog-full-grid { grid-template-columns: repeat(3, 1fr); }
                }
                @media (max-width: 768px) {
                    .blog-full-grid { grid-template-columns: repeat(2, 1fr); }
                }
                @media (max-width: 600px) {
                    .blog-full-grid {
                        grid-template-columns: 1fr;
                        gap: 8px;
                    }
                    /* Horizontal card layout on mobile */
                    .blog-card {
                        flex-direction: row;
                        align-items: stretch;
                        min-height: 100px;
                    }
                    .blog-card-img {
                        width: 110px;
                        height: auto;
                        min-height: 100px;
                        flex-shrink: 0;
                    }
                    .blog-card-title {
                        font-size: 13px;
                        -webkit-line-clamp: 2;
                    }
                    /* Pagination: hide page numbers, show x/y indicator */
                    .page-numbers { display: none; }
                    .page-indicator { display: inline; }
                    .pagination-bar {
                        justify-content: space-between;
                        margin-top: 20px;
                    }
                }
            `}</style>
        </main>
    )
}