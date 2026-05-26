import Link from 'next/link'

const GENRES = [
    'Action', 'Thriller', 'Horror', 'Crime', 'Drama', 'Family',
    'Fantasy', 'Korean', 'Sci-Fi', 'Romance', 'Animation',
    'Chinese', 'War', 'History', 'Mystery', 'Adventure', 'Nollywood'
]

export default function TagCloud() {
    return (
        <div style={{
            padding: '8px 4px',
            background: 'var(--white)',
            border: '1px solid var(--border)'
        }}>
            {GENRES.map(genre => (
                <Link
                    key={genre}
                    href={`/tag/${genre.toLowerCase()}`}
                    style={{
                        display: 'inline-block',
                        fontSize: '12px',
                        border: '1px solid #aac0ff',
                        margin: '3px',
                        padding: '3px 10px',
                        color: 'var(--blue)',
                        background: 'var(--blue-light)',
                        borderRadius: '20px',
                    }}
                >
                    {genre}
                </Link>
            ))}
        </div>
    )
}