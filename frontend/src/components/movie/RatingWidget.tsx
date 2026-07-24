'use client'

import { useState, useEffect } from 'react'

interface Props {
    slug: string
    initialAverage?: number
    initialCount?: number
}

export default function RatingWidget({ slug, initialAverage = 4.3, initialCount = 128 }: Props) {
    const [hover, setHover] = useState(0)
    const [userRating, setUserRating] = useState(0)
    const [average, setAverage] = useState(initialAverage)
    const [count, setCount] = useState(initialCount)

    useEffect(() => {
        const saved = localStorage.getItem(`rating:${slug}`)
        if (saved) setUserRating(Number(saved))
    }, [slug])

    function handleRate(value: number) {
        if (userRating) return // one vote per browser
        const newCount = count + 1
        const newAverage = ((average * count) + value) / newCount
        setUserRating(value)
        setAverage(newAverage)
        setCount(newCount)
        localStorage.setItem(`rating:${slug}`, String(value))
        // TODO: POST { slug, value } to your API to persist server-side
    }

    return (
        <div style={{
            background: 'var(--white)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            padding: '16px',
            marginBottom: '16px',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: '2px' }}>
                    {[1, 2, 3, 4, 5].map(star => (
                        <span
                            key={star}
                            onMouseEnter={() => !userRating && setHover(star)}
                            onMouseLeave={() => !userRating && setHover(0)}
                            onClick={() => handleRate(star)}
                            style={{
                                fontSize: '26px',
                                cursor: userRating ? 'default' : 'pointer',
                                color: star <= (hover || userRating) ? '#f5a623' : '#d9d9d9',
                                transition: 'color 0.15s',
                            }}
                        >
                            ★
                        </span>
                    ))}
                </div>

                <div style={{ fontSize: '14px', color: 'var(--muted)' }}>
                    <strong style={{ color: 'var(--blue-dark)' }}>{average.toFixed(1)}/5</strong>
                    {' '}from {count.toLocaleString()} votes
                    {userRating > 0 && (
                        <span style={{ marginLeft: '8px', color: '#2e7d32' }}>
                            · You rated {userRating}★
                        </span>
                    )}
                </div>
            </div>
        </div>
    )
}