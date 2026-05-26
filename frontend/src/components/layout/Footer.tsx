import Link from 'next/link'

export default function Footer() {
    return (
        <footer style={{
            background: 'var(--blue-dark)',
            borderTop: '4px solid var(--red)',
            padding: '20px 16px',
            textAlign: 'center',
            marginTop: '24px',
        }}>
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: '8px',
                marginBottom: '14px',
            }}>
                {[
                    { label: 'Contact', href: '/contact' },
                    { label: 'DMCA', href: '/dmca' },
                    { label: 'Disclaimer', href: '/disclaimer' },
                    { label: 'Privacy Policy', href: '/privacy-policy' },
                ].map(link => (
                    <Link key={link.href} href={link.href} style={{
                        color: '#aac0ff',
                        padding: '6px 14px',
                        fontSize: '13px',
                        border: '1px solid #334499',
                        borderRadius: '3px',
                        minHeight: '36px',
                        display: 'flex',
                        alignItems: 'center',
                    }}>
                        {link.label}
                    </Link>
                ))}
            </div>
            <p style={{ color: '#aac0ff', fontSize: '13px' }}>
                Copyright &copy; 2026 |{' '}
                <Link href="/" style={{ color: 'var(--red-light)' }}>9janetmovies</Link>
            </p>
        </footer>
    )
}