// components/AdcashScript.tsx
'use client'

import Script from 'next/script'

export default function AdcashScript() {
  return (
    <Script
      id="aclib"
      src="https://acscdn.com/script/aclib.js"
      strategy="afterInteractive"
      onLoad={() => {
        // @ts-expect-error - aclib is injected globally by the script above
        window.aclib?.runAutoTag({
          zoneId: 'llpnfj23jm',
        })
      }}
    />
  )
}