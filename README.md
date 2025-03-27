# Gutenberg Book Analysis

A web application that allows users to explore and analyze books from Project Gutenberg using LLMs. The application identifies characters and their relationships, visualizes character networks, analyzes themes and sentiment, and extracts key quotes from literary works.

## Features

- **Book Search**: Find books from Project Gutenberg by ID
- **Character Identification**: Automatically identify characters in the text
- **Relationship Mapping**: Analyze and visualize relationships between characters
- **Network Visualization**: Interactive graph of character interactions
- **Thematic Analysis**: Extract key themes and sentiment
- **Quote Extraction**: Identify and contextualize significant quotes

## Live Demo

[View the live application](https://gutenberg-analysis-frontend.fly.dev/)

## Tech Stack

### Backend
- Python 3.10+
- FastAPI
- Groq LLM API for text analysis
- BeautifulSoup for HTML parsing
- NetworkX for graph data processing

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- React Force Graph for network visualization

## Project Structure

```
gutenberg-analysis/
├── README.md
├── backend
│   ├── Dockerfile
│   ├── fly.toml
│   ├── __init__.py
│   ├── analysis.py
│   ├── app.py
│   ├── gutenberg.py
│   ├── requirements.txt
│   └── tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_analysis.py
│       ├── test_app.py
│       └── test_gutenberg.py
├── docker-compose.yml
└── frontend
    ├── Dockerfile
    ├── fly.toml
    ├── components
    │   ├── BookAnalysis.tsx
    │   ├── BookFetchingState.tsx
    │   ├── BookHistory.tsx
    │   ├── CharacterGraph.tsx
    │   ├── ExportButton.tsx
    │   ├── Footer.tsx
    │   ├── LoadingState.tsx
    │   ├── NavBar.tsx
    │   ├── ThemeProvider.tsx
    │   ├── ThemeToggle.tsx
    │   └── ui
    │       └── index.tsx
    ├── next-env.d.ts
    ├── next.config.js
    ├── package-lock.json
    ├── package.json
    ├── pages
    │   ├── _app.tsx
    │   └── index.tsx
    ├── postcss.config.js
    ├── public
    ├── styles
    │   └── globals.css
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── tsconfig.tsbuildinfo
    ├── types
    │   └── index.ts
    └── utils
        ├── api.ts
        ├── bookHistory.ts
        ├── cn.ts
        └── eventStream.ts
```

## Local Development

### Prerequisites
- Node.js 20+
- Python 3.10+
- A Groq API key (sign up at https://groq.com/)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. Run the backend server:
   ```bash
   python app.py
   ```

   The backend will run on http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

   The frontend will run on http://localhost:3000

## Docker Deployment

For a containerized setup, you can use Docker Compose:

1. Create a `.env` file in the root directory:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

   The application will be available at http://localhost:3000

## How It Works

1. **Book Retrieval**: The application fetches book content from Project Gutenberg's API
2. **Text Analysis**: The content is analyzed using Groq's LLM API
3. **Character Identification**: The LLM identifies characters and their relationships
4. **Network Building**: A graph database is constructed to represent character relationships
5. **Thematic Analysis**: The LLM extracts themes, sentiment, and key quotes
6. **Visualization**: The frontend displays the analysis results in an interactive interface

## Example Analysis

### Character Network for "Romeo and Juliet"

The application can visualize the complex relationships between characters in Shakespeare's Romeo and Juliet, highlighting:

- The central roles of Romeo and Juliet
- The antagonistic relationship between the Montagues and Capulets
- The supporting relationships of characters like Mercutio, Tybalt, and the Nurse

### Thematic Analysis

For "Pride and Prejudice," the system might identify themes such as:

- Social class and status
- Marriage and relationships
- Personal growth and self-discovery
- Prejudice and first impressions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Tools used

- [Project Gutenberg](https://www.gutenberg.org/) for providing free access to literary works
- [Groq](https://groq.com/) for their powerful LLM API
- [React Force Graph](https://github.com/vasturiano/react-force-graph) for the network visualization library
