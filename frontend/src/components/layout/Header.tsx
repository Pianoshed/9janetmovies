'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import Link from 'next/link'

const GENRES = [
    'Series', 'Action', 'Thriller', 'Horror', 'Crime', 'Drama',
    'Family', 'Fantasy', 'Korean', 'Sci-Fi', 'Romance',
    'Animation', 'Chinese', 'Nollywood', 'Upcoming'
]

export default function Header() {
    const [query, setQuery] = useState('')
    const [menuOpen, setMenuOpen] = useState(false)
    const router = useRouter()

    function handleSearch(e: React.FormEvent) {
        e.preventDefault()
        const trimmed = query.trim()
        if (trimmed) {
            router.push(`/search?q=${encodeURIComponent(trimmed)}`)
            // Don't clear query — user can see what they searched
            // and can edit it for a new search
        }
    }

    return (
        <header style={{ background: 'var(--blue-dark)', borderBottom: '4px solid var(--red)' }}>

            {/* TOP BAR */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '12px 14px',
                position: 'relative',
            }}>
                {/* Logo — always centered */}
                <Link href="/" style={{
                    fontSize: 'clamp(1.6rem, 6vw, 2.4rem)',
                    fontWeight: 700,
                    color: 'var(--white)',
                    letterSpacing: '-1px',
                    lineHeight: 1,
                    textAlign: 'center',
                }}>
                    9janet<span style={{ color: 'var(--red-light)' }}>movies</span>
                </Link>

                {/* Subtitle — desktop only */}
                <div style={{
                    position: 'absolute',
                    right: '14px',
                    color: '#aac0ff',
                    fontSize: '11px',
                    letterSpacing: '2px',
                    textTransform: 'uppercase',
                }} className="header-subtitle">
                    Free Movie Downloads
                </div>

                {/* Hamburger — mobile only */}
                <button
                    onClick={() => setMenuOpen(o => !o)}
                    aria-label="Toggle menu"
                    style={{
                        position: 'absolute',
                        right: '14px',
                        display: 'none',
                        background: 'none',
                        border: '1px solid rgba(255,255,255,0.3)',
                        borderRadius: '4px',
                        padding: '6px 10px',
                        cursor: 'pointer',
                        color: 'var(--white)',
                        fontSize: '20px',
                        lineHeight: 1,
                    }}
                    className="hamburger"
                >
                    {menuOpen ? '✕' : '☰'}
                </button>
            </div>

            {/* SEARCH — centered */}
            <div style={{ padding: '0 14px 12px', background: 'var(--blue-dark)' }}>
                <form onSubmit={handleSearch} style={{
                    display: 'flex',
                    width: '100%',
                    maxWidth: '560px',
                    margin: '0 auto',
                }}>
                    <input
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Search movies, series..."
                        style={{
                            flex: 1,
                            padding: '11px 14px',
                            border: '2px solid var(--blue-mid)',
                            borderRight: 'none',
                            borderRadius: '3px 0 0 3px',
                            fontFamily: 'inherit',
                            fontSize: '15px',
                            minWidth: 0,
                        }}
                    />
                    <button type="submit" style={{
                        padding: '11px 18px',
                        background: 'var(--red)',
                        color: 'var(--white)',
                        border: '2px solid var(--red)',
                        borderRadius: '0 3px 3px 0',
                        fontFamily: 'inherit',
                        fontSize: '14px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        flexShrink: 0,
                    }}>
                        Search
                    </button>
                </form>
            </div>

            {/* NAV GENRES — centered */}
            <nav
                className={`genre-nav${menuOpen ? ' open' : ''}`}
                style={{
                    background: 'var(--red)',
                    padding: '6px 8px',
                    borderBottom: '2px solid var(--red-dark)',
                    overflowX: 'auto',
                    whiteSpace: 'nowrap',
                    textAlign: 'center',
                    WebkitOverflowScrolling: 'touch',
                    scrollbarWidth: 'none',
                }}
            >
                {GENRES.map(genre => (
                    <Link
                        key={genre}
                        href={genre === 'Series' ? '/series' : `/tag/${genre.toLowerCase()}`}
                        onClick={() => setMenuOpen(false)}
                        style={{
                            display: 'inline-block',
                            border: '1px solid var(--red-light)',
                            margin: '3px',
                            padding: '5px 12px',
                            color: 'var(--white)',
                            background: 'var(--red-dark)',
                            borderRadius: '3px',
                            fontSize: '13px',
                            minHeight: '32px',
                            lineHeight: '22px',
                        }}
                    >
                        {genre}
                    </Link>
                ))}
            </nav>

            <style>{`
                @media (max-width: 600px) {
                    .hamburger { display: block !important; }
                    .header-subtitle { display: none !important; }
                    .genre-nav {
                        display: none;
                        white-space: normal !important;
                        text-align: center !important;
                    }
                    .genre-nav.open { display: block !important; }
                }
                .genre-nav::-webkit-scrollbar { display: none; }
            `}</style>
        </header>
    )
}