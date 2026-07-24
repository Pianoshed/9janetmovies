interface Props {
    channelUrl?: string
}

export default function TelegramBanner({ channelUrl = 'https://t.me/naijanetmovies' }: Props) {
    return (
        <div style={{
            background: '#e7f6fd',
            border: '1px solid #a9dcf2',
            borderRadius: '4px',
            padding: '16px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            flexWrap: 'wrap',
        }}>
            <span style={{ fontSize: '32px' }}>📲</span>
            <div style={{ flex: '1 1 200px' }}>
                <p style={{ margin: 0, fontWeight: 700, fontSize: '14px', color: 'var(--blue-dark)' }}>
                    Never miss a new release
                </p>
                <p style={{ margin: '2px 0 0', fontSize: '13px', color: 'var(--muted)' }}>
                    Join our Telegram channel for instant download links.
                </p>
            </div>

            <a href={channelUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                    background: '#229ED9',
                    color: '#fff',
                    padding: '10px 18px',
                    borderRadius: '4px',
                    fontSize: '14px',
                    fontWeight: 600,
                    textDecoration: 'none',
                    whiteSpace: 'nowrap',
                }}
            >
                Follow on Telegram
            </a>
        </div >
    )
}