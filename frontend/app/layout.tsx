import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NYC AI Accountability Portal',
  description: 'Public transparency tool for NYC agency AI system disclosures and bias signals.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
