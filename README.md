# Ultimate SEO Auditor

A comprehensive SEO audit tool built with Streamlit that analyzes Screaming Frog crawl exports and generates AI-powered optimization recommendations.

## Features

### Core Analysis
- **Technical SEO Audit**: Status codes, canonicals, redirects, Core Web Vitals, security checks
- **On-Page SEO Audit**: Titles, meta descriptions, H1s, content quality, internal linking, images
- **Backlink Analysis** (optional): Anchor text distribution, domain quality, toxic link detection
- **Competitor Analysis** (optional): Keyword gaps, quick wins, market positioning

### AI-Powered Recommendations
- Uses OpenRouter to access Claude, GPT-4, or Gemini models
- Expert-level analysis based on embedded SEO knowledge
- Actionable recommendations with prioritization

### Data Sources
- Screaming Frog CSV/Excel exports (55+ columns mapped)
- Google Search Console integration data
- PageSpeed Insights integration data
- Google Analytics 4 integration data

### Reports
- Health score with letter grade (A-F)
- Issues grouped by severity (Critical, High, Medium, Low, Insight)
- Export to Markdown, HTML, or CSV

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SEOptimize-LLC/Ultimate-SEO-Audit-App.git
   cd Ultimate-SEO-Audit-App
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   ```bash
   mkdir .streamlit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   Edit `.streamlit/secrets.toml` with your API credentials:
   ```toml
   OPENROUTER_API_KEY = "your-openrouter-api-key"
   DATAFORSEO_LOGIN = "your-dataforseo-email"
   DATAFORSEO_PASSWORD = "your-dataforseo-password"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

1. **Export from Screaming Frog**: Run a crawl and export as CSV or Excel
   - Enable GSC, PageSpeed, and GA4 integrations for richer analysis

2. **Upload the file**: Use the uploader in the app

3. **Configure options**:
   - Enable/disable backlink and competitor analysis in the sidebar
   - Select your preferred LLM model

4. **Run the audit**: Click "Run SEO Audit"

5. **Review & Export**: Browse issues by category and download reports

## Project Structure

```
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── models/
│   └── audit_result.py       # Data models (Severity, AuditIssue, etc.)
├── utils/
│   └── file_parser.py        # Screaming Frog export parser
├── auditors/
│   ├── base_auditor.py       # Abstract base class
│   ├── technical_auditor.py  # Technical SEO checks
│   ├── onpage_auditor.py     # On-Page SEO checks
│   ├── backlink_auditor.py   # Backlink analysis
│   └── competitor_auditor.py # Competitor analysis
├── services/
│   ├── dataforseo_client.py  # DataForSEO API client
│   ├── openrouter_client.py  # LLM API client
│   └── report_generator.py   # Report generation
├── prompts/
│   ├── technical_prompt.py   # Technical SEO expertise
│   ├── onpage_prompt.py      # On-Page SEO expertise
│   ├── backlink_prompt.py    # Backlink analysis expertise
│   └── competitor_prompt.py  # Competitive analysis expertise
├── Skills/                   # SEO knowledge base (used to build prompts)
└── Documents/                # Additional documentation
```

## API Requirements

### Required
- **OpenRouter API Key**: For AI-powered recommendations
  - Sign up at [openrouter.ai](https://openrouter.ai)
  - Supports Claude, GPT-4, Gemini Pro models

### Optional
- **DataForSEO Credentials**: For backlink and competitor analysis
  - Sign up at [dataforseo.com](https://dataforseo.com)
  - Requires Backlinks API and Labs API access

## Audit Checks

### Technical SEO (20+ checks)
- 4xx/5xx errors
- Noindex pages with content
- Missing/duplicate/chained canonicals
- Redirect chains and loops
- Core Web Vitals (LCP, CLS, TBT)
- HTTPS/security issues
- Slow response times

### On-Page SEO (20+ checks)
- Missing/duplicate/short/long titles
- Missing/duplicate meta descriptions
- Missing/multiple H1 tags
- Thin content (<300 words)
- Low readability scores
- Orphan pages and internal linking issues
- Missing image alt text
- GSC-based CTR opportunities

### Backlink Analysis
- Anchor text distribution
- Over-optimization detection
- Domain diversity
- Low-quality domain detection
- Dofollow/nofollow ratio
- Toxic link patterns

### Competitor Analysis
- Top competitor identification
- Keyword portfolio analysis
- Quick wins (position 4-20)
- Weak ranking keywords
- Content hub identification

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
