// app/contact/page.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Contact — 9janetmovies',
}

export default function ContactPage() {
    return (
        <div style={{ maxWidth: '800px', margin: '24px auto', padding: '0 12px' }}>
            <div style={{
                background: 'var(--white)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                padding: '24px',
            }}>
                <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--blue-dark)', marginBottom: '16px' }}>
                    Contact Us
                </h1>
                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '16px' }}>
                    Have a question, suggestion, or want to report a broken link? Reach out to us using the details below.
                </p>

                <div style={{
                    background: 'var(--grey)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    padding: '16px',
                    marginBottom: '16px',
                }}>
                    <p style={{ fontSize: '14px', color: '#333', marginBottom: '8px' }}>
                        📧 <strong>Email:</strong> admin@9janetmovies.com
                    </p>
                    <p style={{ fontSize: '14px', color: '#333' }}>
                        ⏱ We typically respond within 24–48 hours.
                    </p>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--muted)', lineHeight: 1.7 }}>
                    For copyright or DMCA concerns, please visit our <a href="/dmca" style={{ color: 'var(--blue)', textDecoration: 'underline' }}>DMCA page</a>. We do not host any files and cannot remove content from third-party servers.
                </p>
            </div>
        </div>
    )
}