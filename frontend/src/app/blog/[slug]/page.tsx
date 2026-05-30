'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000/api'

interface BlogPost {
    id: number
    title: string
    slug: string
    summary: string
    content: string | null
    image_url: string | null
    source_name: string
    source_url: string
    category: string
    published_at: string
}

const CATEGORY_COLORS: Record<string, string> = {
    Celebrity: '#e53935',
    Music: '#8B1A1A',
    Entertainment: '#1565c0',
    General: '#2e7d32',
    Nollywood: '#6a1b9a',
}

function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-NG', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    })
}

function timeAgo(dateStr: string) {
    const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
    if (diff < 60) return 'just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

export default function BlogPostPage() {
    const params = useParams()
    const slug = params?.slug as string

    const [post, setPost] = useState<BlogPost | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [showIframe, setShowIframe] = useState(false)
    const [iframeLoading, setIframeLoading] = useState(false)

    useEffect(() => {
        if (!slug) return
        fetch(`${API}/blog/${slug}`)
            .then(r => {
                if (!r.ok) throw new Error('Not found')
                return r.json()
            })
            .then(data => {
                setPost(data)
                setLoading(false)
            })
            .catch(() => {
                setError(true)
                setLoading(false)
            })
    }, [slug])

    if (loading) return (
        <div className="bp-loading">
            <div className="bp-spinner" />
            <p>Loading article...</p>
            <style>{loadingStyles}</style>
        </div>
    )

    if (error || !post) return (
        <div className="bp-error">
            <span>404</span>
            <p>Article not found.</p>
            <Link href="/blog">← Back to Blog</Link>
            <style>{errorStyles}</style>
        </div>
    )

    const catColor = CATEGORY_COLORS[post.category] ?? '#555'
    const hasFullContent = post.content && post.content.length > 100
    const displayContent = post.content || post.summary

    return (
        <>
            <style>{pageStyles(catColor)}</style>

            <div className="bp-wrap">

                {/* HERO */}
                <div className="bp-hero">
                    {post.image_url && (
                        <div className="bp-hero-img">
                            <img
                                src={post.image_url}
                                alt={post.title}
                                onError={e => {
                                    const el = (e.target as HTMLImageElement).closest('.bp-hero-img') as HTMLElement
                                    if (el) el.style.display = 'none'
                                }}
                            />
                            <div className="bp-hero-overlay" />
                        </div>
                    )}
                    <div className="bp-hero-content">
                        <Link href="/blog" className="bp-back">← Entertainment News</Link>
                        <div className="bp-meta-row">
                            <span className="bp-cat" style={{ background: catColor }}>{post.category}</span>
                            <span className="bp-source">{post.source_name}</span>
                            <span className="bp-dot">·</span>
                            <span className="bp-time" title={formatDate(post.published_at)}>
                                {timeAgo(post.published_at)}
                            </span>
                        </div>
                        <h1 className="bp-title">{post.title}</h1>
                        <p className="bp-subtitle">{post.summary}</p>
                    </div>
                </div>

                {/* BODY */}
                <div className="bp-body">

                    {hasFullContent ? (
                        <div className="bp-content">
                            {displayContent!.split('\n').filter(Boolean).map((para, i) => (
                                <p key={i}>{para}</p>
                            ))}
                        </div>
                    ) : (
                        <div className="bp-summary-card">
                            <div className="bp-summary-label">📰 Article Summary</div>
                            <p>{post.summary}</p>
                            <p className="bp-summary-note">
                                Full article content is being fetched. Reload in a few seconds, or read the original below.
                            </p>
                        </div>
                    )}

                    {/* Action buttons */}
                    <div className="bp-actions">
                        <a
                            href={post.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bp-btn-primary"
                        >
                            Read Full Article on {post.source_name} →
                        </a>
                        <button
                            className="bp-btn-secondary"
                            onClick={() => {
                                setShowIframe(true)
                                setIframeLoading(true)
                            }}
                        >
                            {showIframe ? '📄 Article Embedded Below' : '🌐 View Article Inline'}
                        </button>
                    </div>

                    {/* Inline iframe */}
                    {showIframe && (
                        <div className="bp-iframe-wrap">
                            <div className="bp-iframe-header">
                                <span>📰 {post.source_name}</span>
                                <button onClick={() => setShowIframe(false)}>✕ Close</button>
                            </div>
                            {iframeLoading && (
                                <div className="bp-iframe-loading">Loading article...</div>
                            )}
                            <iframe
                                src={post.source_url}
                                title={post.title}
                                onLoad={() => setIframeLoading(false)}
                                style={{ display: iframeLoading ? 'none' : 'block' }}
                            />
                            <div className="bp-iframe-notice">
                                ⚠️ Some sites block embedding. If blank,{' '}
                                <a href={post.source_url} target="_blank" rel="noopener noreferrer">
                                    open in new tab →
                                </a>
                            </div>
                        </div>
                    )}

                    {/* Footer */}
                    <div className="bp-footer">
                        <div className="bp-footer-date">🗓️ {formatDate(post.published_at)}</div>
                        <div className="bp-footer-source">
                            Source:{' '}
                            <a href={post.source_url} target="_blank" rel="noopener noreferrer">
                                {post.source_name}
                            </a>
                        </div>
                    </div>

                </div>
            </div>
        </>
    )
}

const pageStyles = (catColor: string) => `
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap');

    .bp-wrap {
        max-width: 820px;
        margin: 0 auto;
        padding-bottom: 60px;
        font-family: 'Source Serif 4', Georgia, serif;
    }
    .bp-hero {
        position: relative;
        min-height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        border-radius: 10px;
        overflow: hidden;
        background: #0d0d0d;
        margin-bottom: 0;
    }
    .bp-hero-img {
        position: absolute;
        inset: 0;
    }
    .bp-hero-img img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.5;
        display: block;
    }
    .bp-hero-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(to bottom, transparent 10%, rgba(0,0,0,0.9) 100%);
    }
    .bp-hero-content {
        position: relative;
        z-index: 2;
        padding: 28px 32px 36px;
        color: #fff;
    }
    .bp-back {
        display: inline-block;
        font-size: 12px;
        color: rgba(255,255,255,0.6);
        text-decoration: none;
        margin-bottom: 16px;
        letter-spacing: 0.5px;
        font-family: sans-serif;
        transition: color 0.2s;
    }
    .bp-back:hover { color: #fff; }
    .bp-meta-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }
    .bp-cat {
        font-size: 10px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #fff;
        font-family: sans-serif;
    }
    .bp-source { font-size: 12px; color: rgba(255,255,255,0.7); font-family: sans-serif; }
    .bp-dot { color: rgba(255,255,255,0.35); font-size: 12px; }
    .bp-time { font-size: 12px; color: rgba(255,255,255,0.55); font-family: sans-serif; }
    .bp-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: clamp(22px, 4vw, 36px);
        font-weight: 800;
        line-height: 1.22;
        margin: 0 0 14px;
        color: #fff;
        text-shadow: 0 2px 12px rgba(0,0,0,0.5);
    }
    .bp-subtitle {
        font-size: 14px;
        line-height: 1.65;
        color: rgba(255,255,255,0.78);
        margin: 0;
        max-width: 620px;
        font-style: italic;
    }

    /* BODY */
    .bp-body {
        padding: 32px 32px 0;
        background: #fff;
        border: 1px solid #e5e5e5;
        border-top: none;
        border-radius: 0 0 10px 10px;
    }

    /* Full content */
    .bp-content p {
        font-size: 16px;
        line-height: 1.9;
        color: #1a1a1a;
        margin: 0 0 20px;
    }
    .bp-content p:first-child::first-letter {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 56px;
        font-weight: 800;
        float: left;
        line-height: 0.82;
        margin: 8px 10px 0 0;
        color: ${catColor};
    }

    /* Summary card */
    .bp-summary-card {
        background: #fafafa;
        border-left: 4px solid ${catColor};
        border-radius: 0 6px 6px 0;
        padding: 20px 24px;
        margin-bottom: 28px;
    }
    .bp-summary-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: ${catColor};
        margin-bottom: 10px;
        font-family: sans-serif;
    }
    .bp-summary-card p {
        font-size: 15px;
        line-height: 1.75;
        color: #333;
        margin: 0 0 10px;
    }
    .bp-summary-note {
        font-size: 12px !important;
        color: #999 !important;
        font-style: italic;
        margin-bottom: 0 !important;
    }

    /* Buttons */
    .bp-actions {
        display: flex;
        gap: 10px;
        margin-bottom: 28px;
        flex-wrap: wrap;
    }
    .bp-btn-primary {
        display: inline-flex;
        align-items: center;
        background: ${catColor};
        color: #fff;
        font-size: 13px;
        font-weight: 700;
        padding: 11px 22px;
        border-radius: 4px;
        text-decoration: none;
        font-family: sans-serif;
        transition: opacity 0.2s;
        letter-spacing: 0.3px;
    }
    .bp-btn-primary:hover { opacity: 0.85; color: #fff; }
    .bp-btn-secondary {
        display: inline-flex;
        align-items: center;
        background: #fff;
        color: #444;
        font-size: 13px;
        font-weight: 600;
        padding: 11px 22px;
        border-radius: 4px;
        border: 1.5px solid #ddd;
        cursor: pointer;
        font-family: sans-serif;
        transition: all 0.2s;
    }
    .bp-btn-secondary:hover { background: #f5f5f5; border-color: #bbb; }

    /* Iframe */
    .bp-iframe-wrap {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 28px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .bp-iframe-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #f7f7f7;
        padding: 10px 16px;
        font-size: 13px;
        font-weight: 600;
        color: #444;
        font-family: sans-serif;
        border-bottom: 1px solid #e5e5e5;
    }
    .bp-iframe-header button {
        background: none;
        border: none;
        cursor: pointer;
        color: #aaa;
        font-size: 13px;
        padding: 0;
        transition: color 0.2s;
    }
    .bp-iframe-header button:hover { color: #e53935; }
    .bp-iframe-loading {
        padding: 48px;
        text-align: center;
        color: #bbb;
        font-size: 13px;
        font-family: sans-serif;
    }
    .bp-iframe-wrap iframe {
        width: 100%;
        height: 620px;
        border: none;
        display: block;
    }
    .bp-iframe-notice {
        padding: 8px 16px;
        font-size: 12px;
        color: #aaa;
        background: #fafafa;
        border-top: 1px solid #eee;
        font-family: sans-serif;
    }
    .bp-iframe-notice a { color: ${catColor}; text-decoration: none; font-weight: 600; }

    /* Footer */
    .bp-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 0 28px;
        border-top: 1px solid #eee;
        font-size: 13px;
        color: #aaa;
        font-family: sans-serif;
        flex-wrap: wrap;
        gap: 8px;
    }
    .bp-footer a { color: ${catColor}; font-weight: 600; text-decoration: none; }
    .bp-footer a:hover { text-decoration: underline; }

    @media (max-width: 640px) {
        .bp-hero { border-radius: 6px; min-height: 300px; }
        .bp-hero-content { padding: 20px 18px 26px; }
        .bp-body { padding: 20px 18px 0; }
        .bp-actions { flex-direction: column; }
        .bp-btn-primary, .bp-btn-secondary { width: 100%; justify-content: center; }
        .bp-iframe-wrap iframe { height: 400px; }
    }
`

const loadingStyles = `
    .bp-loading {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 80px 20px; gap: 16px;
        color: #bbb; font-family: sans-serif; font-size: 14px;
    }
    .bp-spinner {
        width: 32px; height: 32px;
        border: 3px solid #eee;
        border-top-color: #e53935;
        border-radius: 50%;
        animation: bpspin 0.7s linear infinite;
    }
    @keyframes bpspin { to { transform: rotate(360deg); } }
`

const errorStyles = `
    .bp-error {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 80px 20px; gap: 12px;
        font-family: sans-serif; text-align: center;
    }
    .bp-error span { font-size: 72px; font-weight: 900; color: #eee; line-height: 1; }
    .bp-error p { color: #999; font-size: 15px; margin: 0; }
    .bp-error a { color: #e53935; font-weight: 600; font-size: 14px; text-decoration: none; }
`