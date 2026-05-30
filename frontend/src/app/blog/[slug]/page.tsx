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
    Music: '#6d4c41',
    Entertainment: '#1565c0',
    General: '#2e7d32',
    Nollywood: '#6a1b9a',
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
        <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--muted)' }}>
            Loading article...
        </div>
    )

    if (error || !post) return (
        <div style={{ padding: '40px 20px', textAlign: 'center' }}>
            <p style={{ color: '#e53935', marginBottom: '12px' }}>Article not found.</p>
            <Link href="/blog" style={{ color: 'var(--red)', fontWeight: 600 }}>← Back to Blog</Link>
        </div>
    )

    const displayContent = post.content || post.summary

    return (
        <main style={{ maxWidth: '760px', margin: '0 auto', padding: '24px 16px' }}>

            {/* Back link */}
            <Link href="/blog" style={{
                fontSize: '13px',
                color: 'var(--red)',
                fontWeight: 600,
                textDecoration: 'none',
                display: 'inline-block',
                marginBottom: '20px',
            }}>
                ← Back to Blog
            </Link>

            {/* Category + meta */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                <span style={{
                    background: CATEGORY_COLORS[post.category] ?? '#555',
                    color: '#fff',
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '3px',
                    textTransform: 'uppercase',
                }}>
                    {post.category}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{post.source_name}</span>
                <span style={{ fontSize: '12px', color: 'var(--muted)' }}>·</span>
                <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{timeAgo(post.published_at)}</span>
            </div>

            {/* Title */}
            <h1 style={{
                fontSize: '22px',
                fontWeight: 800,
                lineHeight: 1.35,
                color: 'var(--blue-dark)',
                margin: '0 0 16px',
            }}>
                {post.title}
            </h1>

            {/* Image */}
            {post.image_url && (
                <div style={{ marginBottom: '20px', borderRadius: '6px', overflow: 'hidden' }}>
                    <img
                        src={post.image_url}
                        alt={post.title}
                        style={{ width: '100%', maxHeight: '420px', objectFit: 'cover', display: 'block' }}
                        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                    />
                </div>
            )}

            {/* Content */}
            <div style={{
                fontSize: '15px',
                lineHeight: 1.75,
                color: '#333',
                whiteSpace: 'pre-wrap',
            }}>
                {displayContent}
            </div>

            {/* Source link */}
            {post.source_url && (
                <div style={{ marginTop: '28px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                    <a
                        href={post.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: '13px', color: 'var(--red)', fontWeight: 600 }}
                    >
                        Read original article on {post.source_name} →
                    </a>
                </div>
            )}
        </main>
    )
}