import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/ThemeProvider';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider defaultTheme="system">
      <Head>
        <title>Gutenberg Book Analysis</title>
        <meta name="description" content="Analyze books from Project Gutenberg using LLM" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className={`${inter.variable} font-sans`}>
        <Component {...pageProps} />
      </main>
    </ThemeProvider>
  );
}