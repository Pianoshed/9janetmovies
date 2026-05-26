// app/disclaimer/page.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Disclaimer — 9janetmovies',
}

export default function DisclaimerPage() {
    return (
        <div style={{ maxWidth: '800px', margin: '24px auto', padding: '0 12px' }}>
            <div style={{
                background: 'var(--white)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                padding: '24px',
            }}>
                <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--blue-dark)', marginBottom: '16px' }}>
                    Disclaimer
                </h1>

                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '12px' }}>
                    9janetmovies is an index and search service. We do not upload, store, or host any movies, series, or media files on our servers.
                </p>

                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '12px' }}>
                    All download links on this site point to third-party file hosting services. We have no control over the availability, accuracy, or legality of content on those external sites.
                </p>

                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '12px' }}>
                    By using this site, you agree that 9janetmovies is not responsible for any content accessed via external links, and that you use those links entirely at your own risk.
                </p>

                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '12px' }}>
                    The movie metadata, posters, and descriptions displayed on this site are sourced from publicly available databases (such as TMDB) and are used for informational purposes only.
                </p>

                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333' }}>
                    If you have any concerns, please contact us via our{' '}
                    <a href="/contact" style={{ color: 'var(--blue)', textDecoration: 'underline' }}>Contact page</a>.
                </p>
            </div>
        </div>
    )
}