'use client'
import { useRouter, useSearchParams } from 'next/navigation'

const FILTERS = [
    'All', 'Action', 'Thriller', 'Horror', 'Drama',
    'Sci-Fi', 'Animation', 'Korean', 'Romance', 'Crime', 'Nollywood'
]

export default function FilterBar() {
    const router = useRouter()
    const params = useSearchParams()
    const active = params.get('genre') || 'All'

    function handleFilter(genre: string) {
        if (genre === 'All') {
            router.push('/')
        } else {
            router.push(`/tag/${genre.toLowerCase()}`)
        }
    }

    return (
        <div style={{
            background: 'var(--white)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            padding: '10px 12px',
            marginBottom: '12px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            alignItems: 'center'
        }}>
            <span style={{
                fontSize: '12px',
                fontWeight: 700,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                marginRight: '4px'
            }}>
                Filter:
            </span>
            {FILTERS.map(genre => (
                <button
                    key={genre}
                    onClick={() => handleFilter(genre)}
                    style={{
                        display: 'inline-block',
                        padding: '4px 12px',
                        fontSize: '12px',
                        fontFamily: 'inherit',
                        border: '1px solid var(--border)',
                        borderRadius: '20px',
                        cursor: 'pointer',
                        background: active === genre ? 'var(--blue)' : 'var(--grey)',
                        color: active === genre ? 'var(--white)' : 'var(--black)',
                        borderColor: active === genre ? 'var(--blue)' : 'var(--border)',
                    }}
                >
                    {genre}
                </button>
            ))}
        </div>
    )
}