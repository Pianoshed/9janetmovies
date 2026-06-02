'use client'

import { useState } from 'react'

interface Subtitle {
    id: string
    file_id: number
    file_name: string
    title: string
    year: string
    language: string
    downloads: number
    release: string
    uploader: string
}

interface Props {
    movieTitle?: string
}

export function SubtitleSearch({ movieTitle = '' }: Props) {
    const [query, setQuery] = useState(movieTitle)
    const [lang, setLang] = useState('en')
    const [results, setResults] = useState<Subtitle[]>([])
    const [loading, setLoading] = useState(false)
    const [downloading, setDownloading] = useState<number | null>(null)
    const [error, setError] = useState('')

    const search = async () => {
        if (!query.trim()) return
        setLoading(true)
        setError('')
        setResults([])
        try {
            const res = await fetch(
                `/api/subtitles/search?query=${encodeURIComponent(query)}&lang=${lang}`
            )
            const data = await res.json()
            if (data.error) throw new Error(data.error)
            setResults(data)
        } catch (e: any) {
            setError(e.message || 'Search failed')
        } finally {
            setLoading(false)
        }
    }

    const download = async (subtitle: Subtitle) => {
        setDownloading(subtitle.file_id)
        setError('')
        try {
            const res = await fetch('/api/subtitles/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_id: subtitle.file_id,
                    file_name: subtitle.file_name || `${subtitle.title}.srt`,
                }),
            })
            if (!res.ok) throw new Error('Download failed')
            const blob = await res.blob()
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = subtitle.file_name || `${subtitle.title}.srt`
            a.click()
            URL.revokeObjectURL(url)
        } catch (e: any) {
            setError(e.message || 'Download failed')
        } finally {
            setDownloading(null)
        }
    }

    return (
        <div className="subtitle-search">
            <div className="subtitle-search__bar">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && search()}
                    placeholder="Search subtitles..."
                    className="subtitle-search__input"
                />
                <select
                    value={lang}
                    onChange={(e) => setLang(e.target.value)}
                    className="subtitle-search__lang"
                    aria-label="Subtitle language"
                >
                    <option value="en">English</option>
                    <option value="fr">French</option>
                    <option value="es">Spanish</option>
                    <option value="ar">Arabic</option>
                    <option value="pt">Portuguese</option>
                    <option value="yo">Yoruba</option>
                </select>
                <button
                    onClick={search}
                    disabled={loading}
                    className="subtitle-search__btn"
                >
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>

            {error && <p className="subtitle-search__error">{error}</p>}

            {results.length > 0 && (
                <ul className="subtitle-search__results">
                    {results.map((sub) => (
                        <li key={sub.id} className="subtitle-search__item">
                            <div className="subtitle-search__item-info">
                                <span className="subtitle-search__item-title">{sub.title}</span>
                                {sub.year && <span className="subtitle-search__item-year">({sub.year})</span>}
                                <span className="subtitle-search__item-meta">
                                    {sub.language.toUpperCase()} · {sub.downloads.toLocaleString()} downloads · {sub.uploader}
                                </span>
                                {sub.release && (
                                    <span className="subtitle-search__item-release">{sub.release}</span>
                                )}
                            </div>
                            <button
                                onClick={() => download(sub)}
                                disabled={downloading === sub.file_id}
                                className="subtitle-search__download-btn"
                            >
                                {downloading === sub.file_id ? 'Downloading...' : '⬇ .srt'}
                            </button>
                        </li>
                    ))}
                </ul>
            )}

            {!loading && results.length === 0 && query && (
                <p className="subtitle-search__empty">No subtitles found. Try a different search.</p>
            )}
        </div>
    )
}