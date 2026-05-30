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
        padding: '6px 12px',
        fontSize: '13px',
        fontWeight: active ? 700 : 500,
        border: `1px solid ${active ? 'var(--red)' : 'var(--border)'}`,
        background: active ? 'var(--red)' : 'transparent',
        color: disabled ? 'var(--muted)' : active ? '#fff' : 'var(--blue-dark)',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
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

    // Page numbers with ellipsis gaps
    const pageNumbers = Array.from({ length: pages }, (_, i) => i + 1)
        .filter(n => n === 1 || n === pages || Math.abs(n - page) <= 1)

    return (
        <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px 16px' }}>

            {/* Header */}
            <div style={{ marginBottom: '20px' }}>
                <Link href="/" style={{ fontSize: '13px', color: 'var(--red)', textDecoration: 'none' }}>
                    ← Back to Home
                </Link>
                <h1 style={{ fontSize: '22px', fontWeight: 700, margin: '8px 0 0', color: 'var(--blue-dark)' }}>
                    🗞️ Entertainment Gist
                </h1>
                {total > 0 && (
                    <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '4px 0 0' }}>
                        {total} posts
                    </p>
                )}
            </div>

            {/* Category filters */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
                {CATEGORIES.map(cat => {
                    const active = (cat === 'All' && !category) || cat === category
                    return (
                        <button
                            key={cat}
                            onClick={() => handleCategory(cat)}
                            style={{
                                padding: '5px 12px',
                                fontSize: '12px',
                                fontWeight: active ? 700 : 500,
                                border: `1px solid ${active ? 'var(--red)' : 'var(--border)'}`,
                                background: active ? 'var(--red)' : 'transparent',
                                color: active ? '#fff' : 'var(--blue-dark)',
                                borderRadius: '20px',
                                cursor: 'pointer',
                            }}
                        >
                            {cat}
                        </button>
                    )
                })}
            </div>

            {/* Posts grid */}
            {loading ? (
                <p style={{ color: 'var(--muted)', fontSize: '14px' }}>Loading...</p>
            ) : posts.length === 0 ? (
                <p style={{ color: 'var(--muted)', fontSize: '14px' }}>No posts found.</p>
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
                            <div style={{ padding: '10px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                                <div style={{ display: 'flex', gap: '6px', marginBottom: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                                    <span style={{
                                        background: CATEGORY_COLORS[post.category] ?? '#555',
                                        color: '#fff', fontSize: '10px', fontWeight: 700,
                                        padding: '2px 6px', borderRadius: '2px', textTransform: 'uppercase',
                                    }}>
                                        {post.category}
                                    </span>
                                    <span style={{ fontSize: '11px', color: 'var(--muted)' }}>{post.source_name}</span>
                                    <span style={{ fontSize: '11px', color: 'var(--muted)', marginLeft: 'auto', whiteSpace: 'nowrap' }}>
                                        {timeAgo(post.published_at)}
                                    </span>
                                </div>
                                <h3 style={{
                                    fontSize: '13px', fontWeight: 600, lineHeight: 1.4,
                                    color: 'var(--blue-dark)', margin: '0 0 6px',
                                    display: '-webkit-box', WebkitLineClamp: 3,
                                    WebkitBoxOrient: 'vertical', overflow: 'hidden',
                                }}>
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '28px', flexWrap: 'wrap' }}>
                    <button
                        onClick={() => setPage(p => p - 1)}
                        disabled={page === 1}
                        style={btnStyle(false, page === 1)}
                    >
                        ← Prev
                    </button>

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

                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={page === pages}
                        style={btnStyle(false, page === pages)}
                    >
                        Next →
                    </button>

                    <span style={{ fontSize: '12px', color: 'var(--muted)', marginLeft: '8px' }}>
                        Page {page} of {pages}
                    </span>
                </div>
            )}

            <style>{`
                .blog-full-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 12px;
                }
                .blog-card {
                    display: flex; flex-direction: column;
                    background: var(--white);
                    border: 1px solid var(--border);
                    border-radius: 4px; overflow: hidden;
                    text-decoration: none; color: inherit;
                    transition: box-shadow 0.15s;
                }
                .blog-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
                .blog-card-img {
                    width: 100%; height: 140px;
                    overflow: hidden; background: #eee; flex-shrink: 0;
                }
                @media (max-width: 1024px) { .blog-full-grid { grid-template-columns: repeat(3, 1fr); } }
                @media (max-width: 900px)  { .blog-full-grid { grid-template-columns: repeat(2, 1fr); } }
                @media (max-width: 600px)  { .blog-full-grid { grid-template-columns: 1fr; } }
            `}</style>
        </main>
    )
}