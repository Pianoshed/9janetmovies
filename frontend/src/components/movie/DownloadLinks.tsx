'use client'
import { DownloadLink } from '@/lib/types'

const HOST_CONFIG: Record<string, { label: string; icon: string; direct: boolean }> = {
    DLDownload: { label: 'DLDownload', icon: '⬇️', direct: true },
    TheNkiri: { label: 'TheNkiri', icon: '⬇️', direct: false },
    MeetDownload: { label: 'MeetDownload', icon: '🎬', direct: false },
}

interface Props {
    links: DownloadLink[]
}

export function DownloadLinks({ links }: Props) {
    if (!links || links.length === 0) {
        return <p className="no-links">No download links available.</p>
    }

    return (
        <div className="download-links">
            {links.map((link, i) => {
                const config = HOST_CONFIG[link.host] ?? { label: link.host, icon: '⬇️', direct: false }
                return (
                    <a
                        key={i}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`download-btn ${link.host.toLowerCase()}`}
                    >
                        {config.icon} {config.label} — {link.label}
                    </a>
                )
            })}
        </div>
    )
}