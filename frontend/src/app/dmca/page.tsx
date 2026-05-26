// app/dmca/page.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'DMCA — 9janetmovies',
}

export default function DMCAPage() {
    return (
        <div style={{ maxWidth: '800px', margin: '24px auto', padding: '0 12px' }}>
            <div style={{
                background: 'var(--white)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                padding: '24px',
            }}>
                <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--blue-dark)', marginBottom: '16px' }}>
                    DMCA Notice
                </h1>
                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '12px' }}>
                    9janetmovies does not host any files on its servers. All content linked on this site points to third-party file hosting services outside our control.
                </p>
                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333', marginBottom: '12px' }}>
                    If you believe that content linked on this site infringes your copyright, please contact the respective file hosting service directly to request removal.
                </p>
                <p style={{ fontSize: '14px', lineHeight: 1.8, color: '#333' }}>
                    For further inquiries, contact us at: <strong>admin@9janetmovies.com</strong>
                </p>
            </div>
        </div>
    )
}