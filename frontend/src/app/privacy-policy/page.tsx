import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Privacy Policy – 9janetmovies',
    description: 'Privacy Policy for 9janetmovies.com.ng — how we collect, use, and protect your data.',
}

const EFFECTIVE_DATE = 'May 30, 2026'
const SITE_NAME = '9janetmovies'
const SITE_URL = 'https://9janetmovies.com.ng'
const CONTACT_EMAIL = '9janetmovies@9janetmovies.com.ng'

export default function PrivacyPolicyPage() {
    return (
        <div style={{ maxWidth: '820px', margin: '24px auto', padding: '0 16px 60px' }}>
            <div style={{
                background: 'var(--white)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                padding: '36px 40px',
            }}>
                <h1 style={{
                    fontSize: '26px',
                    fontWeight: 800,
                    color: 'var(--blue-dark)',
                    marginBottom: '6px',
                }}>
                    Privacy Policy
                </h1>
                <p style={{ fontSize: '13px', color: '#888', marginBottom: '32px' }}>
                    Effective Date: {EFFECTIVE_DATE} &nbsp;·&nbsp; Last Updated: {EFFECTIVE_DATE}
                </p>

                <Section title="1. Introduction">
                    <p>
                        Welcome to <strong>{SITE_NAME}</strong> ("{SITE_URL}"). We are committed to protecting your
                        personal information and your right to privacy. This Privacy Policy explains what information
                        we collect, how we use it, and what rights you have in relation to it.
                    </p>
                    <p>
                        By using our website, you agree to the collection and use of information in accordance with
                        this policy. If you do not agree, please do not use our services.
                    </p>
                </Section>

                <Section title="2. Information We Collect">
                    <p>We may collect the following types of information:</p>
                    <ul>
                        <li><strong>Usage Data:</strong> Pages visited, time spent on pages, browser type, device type, IP address, and referring URLs — collected automatically via server logs and analytics tools.</li>
                        <li><strong>Contact Information:</strong> If you submit our contact form, we collect your name and email address to respond to your inquiry.</li>
                        <li><strong>Cookies &amp; Tracking:</strong> We use cookies and similar technologies to improve your browsing experience and analyse site traffic.</li>
                        <li><strong>Search Queries:</strong> Search terms entered on our site may be logged to improve search functionality.</li>
                    </ul>
                    <p>We do <strong>not</strong> collect payment information, passwords, or sensitive personal data.</p>
                </Section>

                <Section title="3. How We Use Your Information">
                    <p>We use the information we collect to:</p>
                    <ul>
                        <li>Operate and maintain our website</li>
                        <li>Analyse usage patterns to improve user experience</li>
                        <li>Respond to contact form submissions</li>
                        <li>Monitor for abuse, spam, or illegal activity</li>
                        <li>Comply with legal obligations</li>
                    </ul>
                    <p>We do <strong>not</strong> sell, trade, or rent your personal information to third parties.</p>
                </Section>

                <Section title="4. Cookies">
                    <p>
                        Our website uses cookies — small text files stored on your device — to enhance functionality
                        and analyse traffic. You can control cookies through your browser settings. Disabling cookies
                        may affect some features of the site.
                    </p>
                    <p>Types of cookies we may use:</p>
                    <ul>
                        <li><strong>Essential cookies:</strong> Required for the site to function properly.</li>
                        <li><strong>Analytics cookies:</strong> Help us understand how visitors interact with the site (e.g. Google Analytics).</li>
                        <li><strong>Preference cookies:</strong> Remember your settings and preferences.</li>
                    </ul>
                </Section>

                <Section title="5. Third-Party Services">
                    <p>
                        Our site contains links to third-party websites and embeds content from external sources.
                        We are not responsible for the privacy practices of those sites. We encourage you to review
                        their privacy policies before providing any personal information.
                    </p>
                    <p>Third-party services we may use include:</p>
                    <ul>
                        <li>Google Analytics — for site traffic analysis</li>
                        <li>External file hosting services — for download links</li>
                        <li>News RSS sources — for entertainment news aggregation</li>
                        <li>TMDB — for movie metadata and poster images</li>
                    </ul>
                </Section>

                <Section title="6. News Content &amp; Aggregation">
                    <p>
                        {SITE_NAME} aggregates entertainment news from publicly available RSS feeds published by
                        third-party news outlets. We display article summaries and link back to original sources.
                        We do not claim ownership of any third-party news content. All rights remain with the
                        original publishers.
                    </p>
                    <p>
                        If you are a content owner and believe your content has been used improperly, please contact
                        us at <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> and we will address it promptly.
                    </p>
                </Section>

                <Section title="7. Data Retention">
                    <p>
                        We retain usage logs and contact form submissions for a maximum of 90 days, after which
                        they are deleted. We do not store personal data longer than necessary for the purposes
                        described in this policy.
                    </p>
                </Section>

                <Section title="8. Data Security">
                    <p>
                        We implement reasonable technical and organisational measures to protect your information
                        from unauthorised access, alteration, disclosure, or destruction. However, no method of
                        transmission over the internet is 100% secure, and we cannot guarantee absolute security.
                    </p>
                </Section>

                <Section title="9. Children's Privacy">
                    <p>
                        Our website is not directed at children under the age of 13. We do not knowingly collect
                        personal information from children. If you believe a child has provided us with personal
                        information, please contact us and we will delete it immediately.
                    </p>
                </Section>

                <Section title="10. Your Rights">
                    <p>Depending on your location, you may have the following rights:</p>
                    <ul>
                        <li><strong>Access:</strong> Request a copy of the personal data we hold about you.</li>
                        <li><strong>Correction:</strong> Request correction of inaccurate data.</li>
                        <li><strong>Deletion:</strong> Request deletion of your personal data.</li>
                        <li><strong>Objection:</strong> Object to processing of your personal data.</li>
                        <li><strong>Portability:</strong> Request transfer of your data in a machine-readable format.</li>
                    </ul>
                    <p>
                        To exercise any of these rights, contact us at{' '}
                        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
                    </p>
                </Section>

                <Section title="11. DMCA &amp; Copyright">
                    <p>
                        {SITE_NAME} respects intellectual property rights. We do not host or store any copyrighted
                        media files. If you believe any content on our site infringes your copyright, please visit
                        our <a href="/dmca">DMCA page</a> or email{' '}
                        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> with details of the alleged
                        infringement.
                    </p>
                </Section>

                <Section title="12. Changes to This Policy">
                    <p>
                        We may update this Privacy Policy from time to time. Changes will be posted on this page
                        with an updated effective date. We encourage you to review this policy periodically.
                        Continued use of the site after changes constitutes acceptance of the updated policy.
                    </p>
                </Section>

                <Section title="13. Contact Us">
                    <p>If you have any questions about this Privacy Policy, please contact us:</p>
                    <ul>
                        <li><strong>Email:</strong> <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a></li>
                        <li><strong>Website:</strong> <a href="/contact">9janetmovies.com.ng/contact</a></li>
                    </ul>
                </Section>

            </div>

            <style>{`
                .pp-section { margin-bottom: 28px; }
                .pp-section h2 {
                    font-size: 15px;
                    font-weight: 700;
                    color: var(--blue-dark);
                    margin-bottom: 10px;
                    padding-bottom: 6px;
                    border-bottom: 1px solid var(--border);
                }
                .pp-section p {
                    font-size: 14px;
                    line-height: 1.85;
                    color: #333;
                    margin-bottom: 10px;
                }
                .pp-section ul {
                    padding-left: 20px;
                    margin-bottom: 10px;
                }
                .pp-section ul li {
                    font-size: 14px;
                    line-height: 1.8;
                    color: #333;
                    margin-bottom: 4px;
                }
                .pp-section a {
                    color: var(--red);
                    text-decoration: underline;
                }
                @media (max-width: 600px) {
                    .pp-wrap { padding: 20px 16px !important; }
                }
            `}</style>
        </div>
    )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="pp-section">
            <h2>{title}</h2>
            {children}
        </div>
    )
}