import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="py-8 border-t mt-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">About Gutenberg Analysis</h3>
            <p className="text-sm text-muted-foreground">
              This application uses AI to analyze any book from Project Gutenberg,
              visualizing character relationships, themes, and narrative elements.
            </p>
          </div>

          {/* Resources section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a 
                  href="https://gutenberg.org" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-muted-foreground hover:text-primary"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                  </svg>
                  Project Gutenberg
                </a>
              </li>
              <li>
                <a 
                  href="https://groq.com/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-muted-foreground hover:text-primary"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                  </svg>
                  Groq LLM
                </a>
              </li>
              <li>
                <a 
                  href="https://github.com/lucashsg77/gutenberg-analysis" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-muted-foreground hover:text-primary"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                  </svg>
                  Source Code
                </a>
              </li>
            </ul>
          </div>

          {/* Keyboard shortcuts section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Keyboard Shortcuts</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center">
                <kbd className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs mr-2">Alt + Click</kbd>
                <span className="text-muted-foreground">Pan graph</span>
              </div>
              <div className="flex items-center">
                <kbd className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs mr-2">Scroll</kbd>
                <span className="text-muted-foreground">Zoom graph</span>
              </div>
              <div className="flex items-center">
                <kbd className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs mr-2">R</kbd>
                <span className="text-muted-foreground">Reset view</span>
              </div>
              <div className="flex items-center">
                <kbd className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs mr-2">Click</kbd>
                <span className="text-muted-foreground">Drag nodes</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-muted text-center text-muted-foreground text-sm">
          <p>
            Book content provided by{' '}
            <a 
              href="https://gutenberg.org" 
              target="_blank" 
              rel="noopener noreferrer"
              className="underline hover:text-primary"
            >
              Project Gutenberg
            </a>
            {' | '}
            Large Language Models powered by{' '}
            <a 
              href="https://groq.com/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="underline hover:text-primary"
            >
              Groq
            </a>
          </p>
          <p className="mt-2">
            © {new Date().getFullYear()} Gutenberg Analysis - Built with Next.js, Tailwind CSS, and shadcn/ui
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;