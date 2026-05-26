import Link from 'next/link'

interface Props {
    children: React.ReactNode
    href?: string
}

export default function WidgetTitle({ children, href }: Props) {
    return (
        <div style={{
            background: 'var(--blue)',
            color: 'var(--white)',
            padding: '9px 12px',
            fontSize: '13px',
            fontWeight: 700,
            letterSpacing: '1px',
            textTransform: 'uppercase',
            borderLeft: '4px solid var(--red)',
            marginBottom: '2px'
        }}>
            {href ? <Link href={href} style={{ color: 'var(--white)' }}>{children}</Link> : children}
        </div>
    )
}