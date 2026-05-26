export default function SectionHeading({ children }: { children: React.ReactNode }) {
    return (
        <div style={{
            background: 'var(--blue)',
            color: 'var(--white)',
            fontSize: '17px',
            fontWeight: 700,
            padding: '9px 14px',
            marginBottom: '10px',
            borderLeft: '5px solid var(--red)',
            borderRadius: '2px',
            letterSpacing: '1px',
            textTransform: 'uppercase'
        }}>
            {children}
        </div>
    )
}