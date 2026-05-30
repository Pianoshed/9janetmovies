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
    source_url: string
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
    Celebrity: '#e53935',
    Music: '#6d4c41',
    Entertainment: '#1565c0',
    General: '#2e7d32',
    Nollywood: '#6a1b9a',
}

export default function BlogSection() {
    const [posts, setPosts] = useState<BlogPost[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch(`${API}/blog?limit=6`)
            .then(r => r.json())
            .then(data => {
                setPosts(data.posts ?? [])
                setLoading(false)
            })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return (
        <div style={{ padding: '16px 0', color: 'var(--muted)', fontSize: '14px' }}>
            Loading latest gist...
        </div>
    )

    if (posts.length === 0) return null

    return (
        <section style={{ marginTop: '28px' }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '12px',
                borderBottom: '2px solid var(--red)',
                paddingBottom: '8px',
            }}>
                <h2 style={{
                    fontSize: '15px',
                    fontWeight: 700,
                    color: 'var(--blue-dark)',
                    margin: 0,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                }}>
                    🗞️ Latest Entertainment Gist
                </h2>

                {/* ── NEW: View All link ── */}
                <Link href="/blog" style={{
                    fontSize: '12px',
                    color: 'var(--red)',
                    fontWeight: 600,
                    textDecoration: 'none',
                    whiteSpace: 'nowrap',
                }}>
                    View All →
                </Link>
            </div>

            <div className="blog-grid">
                {posts.map(post => (
                    <Link
                        key={post.id}
                        href={`/blog/${post.slug}`}
                        className="blog-card"
                    >
                        {post.image_url && (
                            <div className="blog-card-img">
                                <img
                                    src={post.image_url}
                                    alt={post.title}
                                    style={{
                                        width: '100%',
                                        height: '100%',
                                        objectFit: 'cover',
                                        display: 'block',
                                    }}
                                    onError={e => {
                                        (e.target as HTMLImageElement).parentElement!.style.display = 'none'
                                    }}
                                />
                            </div>
                        )}

                        <div style={{
                            padding: '10px',
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                        }}>
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                marginBottom: '6px',
                                flexWrap: 'wrap',
                            }}>
                                <span style={{
                                    background: CATEGORY_COLORS[post.category] ?? '#555',
                                    color: '#fff',
                                    fontSize: '10px',
                                    fontWeight: 700,
                                    padding: '2px 6px',
                                    borderRadius: '2px',
                                    textTransform: 'uppercase',
                                }}>
                                    {post.category}
                                </span>
                                <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                                    {post.source_name}
                                </span>
                                <span style={{
                                    fontSize: '11px',
                                    color: 'var(--muted)',
                                    marginLeft: 'auto',
                                    whiteSpace: 'nowrap',
                                }}>
                                    {timeAgo(post.published_at)}
                                </span>
                            </div>

                            <h3 style={{
                                fontSize: '13px',
                                fontWeight: 600,
                                lineHeight: 1.4,
                                color: 'var(--blue-dark)',
                                margin: '0 0 6px',
                                display: '-webkit-box',
                                WebkitLineClamp: 3,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                            }}>
                                {post.title}
                            </h3>

                            {post.summary && (
                                <p className="blog-summary" style={{
                                    fontSize: '12px',
                                    color: '#555',
                                    lineHeight: 1.5,
                                    margin: 0,
                                    display: '-webkit-box',
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: 'vertical',
                                    overflow: 'hidden',
                                }}>
                                    {post.summary}
                                </p>
                            )}

                            <div style={{
                                marginTop: 'auto',
                                paddingTop: '8px',
                                fontSize: '12px',
                                color: 'var(--red)',
                                fontWeight: 600,
                            }}>
                                Read more →
                            </div>
                        </div>
                    </Link>
                ))}
            </div>

            <style>{`
                .blog-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
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
                .blog-card:hover {
                    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                }
                .blog-card-img {
                    width: 100%;
                    height: 140px;
                    overflow: hidden;
                    background: #eee;
                    flex-shrink: 0;
                }
                @media (max-width: 900px) {
                    .blog-grid { grid-template-columns: repeat(2, 1fr); }
                }
                @media (max-width: 600px) {
                    .blog-grid { grid-template-columns: 1fr; gap: 10px; }
                    .blog-card { flex-direction: row; align-items: flex-start; }
                    .blog-card-img { width: 110px; height: 90px; flex-shrink: 0; }
                    .blog-summary { display: none !important; }
                }
            `}</style>
        </section>
    )
}