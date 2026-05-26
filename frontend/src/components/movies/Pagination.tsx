import Link from 'next/link'

interface Props {
    current: number
    total: number
    basePath?: string
}

function pageHref(basePath: string, page: number): string {
    if (page === 1) return '/'
    if (basePath) return `/${basePath}/${page}`
    return `/${page}`
}

function getPageNumbers(current: number, total: number): (number | '...')[] {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

    const pages: (number | '...')[] = [1]

    if (current > 3) pages.push('...')

    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) pages.push(i)

    if (current < total - 2) pages.push('...')

    pages.push(total)
    return pages
}

export default function Pagination({ current, total, basePath = '' }: Props) {
    if (total <= 1) return null

    const pages = getPageNumbers(current, total)

    return (
        <nav style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '4px',
            margin: '16px 0',
        }}>
            {/* Prev */}
            {current > 1 ? (
                <Link href={pageHref(basePath, current - 1)} style={linkStyle}>
                    &laquo;
                </Link>
            ) : (
                <span style={disabledStyle}>&laquo;</span>
            )}

            {/* Page numbers */}
            {pages.map((page, i) =>
                page === '...' ? (
                    <span key={`dots-${i}`} style={dotsStyle}>…</span>
                ) : page === current ? (
                    <span key={page} style={activeStyle}>{page}</span>
                ) : (
                    <Link key={page} href={pageHref(basePath, page)} style={linkStyle}>
                        {page}
                    </Link>
                )
            )}

            {/* Next */}
            {current < total ? (
                <Link href={pageHref(basePath, current + 1)} style={linkStyle}>
                    &raquo;
                </Link>
            ) : (
                <span style={disabledStyle}>&raquo;</span>
            )}
        </nav>
    )
}

const base: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: '36px',
    height: '36px',
    padding: '0 10px',
    border: '1px solid var(--border)',
    fontSize: '14px',
    borderRadius: '3px',
}

const linkStyle: React.CSSProperties = {
    ...base,
    background: 'var(--white)',
    color: 'var(--black)',
}

const activeStyle: React.CSSProperties = {
    ...base,
    background: 'var(--blue)',
    color: 'var(--white)',
    borderColor: 'var(--blue)',
    fontWeight: 700,
}

const disabledStyle: React.CSSProperties = {
    ...base,
    background: 'var(--grey)',
    color: 'var(--muted)',
    cursor: 'not-allowed',
}

const dotsStyle: React.CSSProperties = {
    ...base,
    border: 'none',
    background: 'none',
    color: 'var(--muted)',
}