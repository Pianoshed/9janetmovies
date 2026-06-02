import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      // TMDB
      { protocol: 'https', hostname: 'image.tmdb.org', pathname: '/t/p/**' },
      { protocol: 'https', hostname: 'www.themoviedb.org' },

      // YouTube thumbnails
      { protocol: 'https', hostname: 'i.ytimg.com' },
      { protocol: 'https', hostname: 'img.youtube.com' },

      // Unsplash
      { protocol: 'https', hostname: 'images.unsplash.com' },

      // TheNkiri (WordPress)
      { protocol: 'https', hostname: 'thenkiri.com' },
      { protocol: 'https', hostname: '**.thenkiri.com' },

      // DLDownload (WordPress)
      { protocol: 'https', hostname: 'dldownload.com.ng' },
      { protocol: 'https', hostname: '**.dldownload.com.ng' },

      // WordPress CDN (used by both sources)
      { protocol: 'https', hostname: '**.wordpress.com' },
      { protocol: 'https', hostname: '**.wp.com' },
      { protocol: 'https', hostname: 'i0.wp.com' },
      { protocol: 'https', hostname: 'i1.wp.com' },
      { protocol: 'https', hostname: 'i2.wp.com' },
    ],
  },
};

export default nextConfig;