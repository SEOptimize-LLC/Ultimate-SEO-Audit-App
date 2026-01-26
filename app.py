"""Ultimate SEO Auditor - Main Streamlit Application.

A comprehensive SEO audit tool that analyzes Screaming Frog crawl exports
and generates AI-powered optimization recommendations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Local imports
from utils.file_parser import (
    parse_screaming_frog_export,
    detect_integrations,
    get_export_summary,
    get_domain_from_urls,
)
from models.audit_result import AuditResult, AuditSummary, Severity
from auditors.technical_auditor import TechnicalAuditor
from auditors.onpage_auditor import OnPageAuditor
from auditors.backlink_auditor import BacklinkAuditor
from auditors.competitor_auditor import CompetitorAuditor
from services.dataforseo_client import DataForSEOClient, BacklinkData, CompetitorData
from services.openrouter_client import OpenRouterClient
from services.report_generator import ReportGenerator
from prompts.technical_prompt import get_technical_prompt, format_technical_issues
from prompts.onpage_prompt import get_onpage_prompt, format_onpage_issues
from prompts.backlink_prompt import get_backlink_prompt, format_backlink_data
from prompts.competitor_prompt import get_competitor_prompt, format_competitor_data

# Page configuration
st.set_page_config(
    page_title="Ultimate SEO Auditor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .severity-critical { color: #dc3545; font-weight: bold; }
    .severity-high { color: #fd7e14; font-weight: bold; }
    .severity-medium { color: #ffc107; }
    .severity-low { color: #17a2b8; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "df": None,
        "audit_result": None,
        "domain": None,
        "integrations": None,
        "audit_complete": False,
        "llm_analysis_complete": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_status() -> dict:
    """Check API availability from secrets."""
    status = {
        "openrouter": False,
        "dataforseo": False,
    }

    try:
        if st.secrets.get("OPENROUTER_API_KEY"):
            status["openrouter"] = True
    except Exception:
        pass

    try:
        if st.secrets.get("DATAFORSEO_LOGIN") and st.secrets.get("DATAFORSEO_PASSWORD"):
            status["dataforseo"] = True
    except Exception:
        pass

    return status


def render_sidebar():
    """Render the sidebar with configuration options."""
    st.sidebar.title("🔍 SEO Auditor")

    # API Status
    st.sidebar.subheader("API Status")
    api_status = get_api_status()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if api_status["openrouter"]:
            st.success("OpenRouter ✓")
        else:
            st.error("OpenRouter ✗")
    with col2:
        if api_status["dataforseo"]:
            st.success("DataForSEO ✓")
        else:
            st.warning("DataForSEO ✗")

    st.sidebar.divider()

    # Model selection
    st.sidebar.subheader("LLM Settings")
    model = st.sidebar.selectbox(
        "Model",
        [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-pro-1.5",
        ],
        index=0,
    )

    st.sidebar.divider()

    # Audit options
    st.sidebar.subheader("Audit Options")

    enable_backlinks = st.sidebar.checkbox(
        "Enable Backlink Analysis",
        value=False,
        disabled=not api_status["dataforseo"],
        help="Requires DataForSEO API credentials",
    )

    enable_competitors = st.sidebar.checkbox(
        "Enable Competitor Analysis",
        value=False,
        disabled=not api_status["dataforseo"],
        help="Requires DataForSEO API credentials",
    )

    enable_llm = st.sidebar.checkbox(
        "Enable AI Recommendations",
        value=True,
        disabled=not api_status["openrouter"],
        help="Requires OpenRouter API key",
    )

    return {
        "model": model,
        "enable_backlinks": enable_backlinks,
        "enable_competitors": enable_competitors,
        "enable_llm": enable_llm,
    }


def render_upload_section():
    """Render the file upload section."""
    st.header("📁 Step 1: Upload Screaming Frog Export")

    uploaded_file = st.file_uploader(
        "Upload your Screaming Frog crawl export (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        help="Export your crawl data from Screaming Frog as CSV or Excel format",
    )

    if uploaded_file:
        with st.spinner("Parsing file..."):
            try:
                # Determine file type
                file_type = uploaded_file.name.split(".")[-1].lower()

                # Parse the file
                df = parse_screaming_frog_export(uploaded_file, file_type)
                st.session_state.df = df

                # Get summary
                summary = get_export_summary(df)
                st.session_state.domain = summary.get("domain")
                st.session_state.integrations = detect_integrations(df)

                st.success(f"✓ Loaded {len(df):,} URLs from {st.session_state.domain or 'Unknown domain'}")

                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total URLs", f"{len(df):,}")
                with col2:
                    st.metric("Columns", f"{len(df.columns)}")
                with col3:
                    gsc = "Yes" if st.session_state.integrations.get("gsc") else "No"
                    st.metric("GSC Data", gsc)
                with col4:
                    ps = "Yes" if st.session_state.integrations.get("pagespeed") else "No"
                    st.metric("PageSpeed Data", ps)

                # Preview
                with st.expander("Preview Data"):
                    st.dataframe(df.head(10), use_container_width=True)

                # Diagnostic info
                with st.expander("🔧 Column Diagnostics (Debug)"):
                    st.markdown("**Mapped Columns:**")
                    key_cols = {
                        "url": "Address/URL",
                        "status_code": "Status Code",
                        "title": "Title",
                        "meta_description": "Meta Description",
                        "h1": "H1",
                        "word_count": "Word Count",
                        "canonical": "Canonical",
                        "indexability": "Indexability",
                        "internal_links_in": "Internal Links In",
                    }
                    col_status = []
                    for std_name, display_name in key_cols.items():
                        exists = std_name in df.columns
                        has_data = False
                        sample = "N/A"
                        if exists:
                            non_null = df[std_name].notna().sum()
                            has_data = non_null > 0
                            if has_data:
                                sample = str(df[std_name].dropna().iloc[0])[:50] if len(df[std_name].dropna()) > 0 else "empty"
                        status = "✅" if exists and has_data else "❌" if not exists else "⚠️ (empty)"
                        col_status.append(f"- {display_name} (`{std_name}`): {status} - Sample: `{sample}`")
                    st.markdown("\n".join(col_status))

                    st.markdown(f"\n**All {len(df.columns)} columns in file:**")
                    st.code(", ".join(df.columns.tolist()))

            except Exception as e:
                st.error(f"Error parsing file: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.session_state.df = None

    return st.session_state.df is not None


def run_audit(options: dict) -> AuditResult:
    """Run the full SEO audit.

    Args:
        options: Audit configuration options

    Returns:
        AuditResult object
    """
    df = st.session_state.df
    domain = st.session_state.domain
    integrations = st.session_state.integrations

    # Initialize summary
    summary = AuditSummary(
        total_urls=len(df),
        domain=domain,
        has_gsc_data=integrations.get("gsc", False),
        has_pagespeed_data=integrations.get("pagespeed", False),
        has_ga4_data=integrations.get("ga4", False),
    )

    result = AuditResult(summary=summary)

    # Progress bar
    progress = st.progress(0)
    status = st.empty()

    # Technical Audit
    status.text("Running technical SEO audit...")
    progress.progress(10)
    technical_auditor = TechnicalAuditor(df)
    result.technical_issues = technical_auditor.run_audit()
    progress.progress(30)

    # On-Page Audit
    status.text("Running on-page SEO audit...")
    onpage_auditor = OnPageAuditor(df)
    result.onpage_issues = onpage_auditor.run_audit()
    progress.progress(50)

    # Backlink Analysis (optional)
    if options.get("enable_backlinks") and domain:
        status.text("Running backlink analysis...")
        try:
            client = DataForSEOClient(
                st.secrets["DATAFORSEO_LOGIN"],
                st.secrets["DATAFORSEO_PASSWORD"],
            )
            backlink_data = client.get_full_backlink_analysis(domain)
            backlink_auditor = BacklinkAuditor(backlink_data, domain)
            result.backlink_issues = backlink_auditor.run_audit()
        except Exception as e:
            st.warning(f"Backlink analysis failed: {str(e)}")
    progress.progress(70)

    # Competitor Analysis (optional)
    if options.get("enable_competitors") and domain:
        status.text("Running competitor analysis...")
        try:
            client = DataForSEOClient(
                st.secrets["DATAFORSEO_LOGIN"],
                st.secrets["DATAFORSEO_PASSWORD"],
            )
            competitor_data = client.get_full_competitor_analysis(domain)
            competitor_auditor = CompetitorAuditor(competitor_data, domain)
            result.competitor_issues = competitor_auditor.run_audit()
        except Exception as e:
            st.warning(f"Competitor analysis failed: {str(e)}")
    progress.progress(85)

    # Update summary with issue counts
    result.summary.update_from_issues(result.all_issues)

    # LLM Analysis (optional)
    if options.get("enable_llm"):
        status.text("Generating AI recommendations...")
        try:
            llm_client = OpenRouterClient(
                st.secrets["OPENROUTER_API_KEY"],
                options.get("model"),
            )

            # Technical analysis
            if result.technical_issues:
                tech_prompt = get_technical_prompt()
                tech_data = format_technical_issues(result.technical_issues)
                response = llm_client.analyze(tech_prompt, tech_data)
                result.technical_analysis = response.content

            # On-page analysis
            if result.onpage_issues:
                onpage_prompt = get_onpage_prompt()
                onpage_data = format_onpage_issues(result.onpage_issues)
                response = llm_client.analyze(onpage_prompt, onpage_data)
                result.onpage_analysis = response.content

        except Exception as e:
            st.warning(f"AI analysis failed: {str(e)}")

    progress.progress(100)
    status.text("Audit complete!")

    return result


def render_results(result: AuditResult):
    """Render the audit results."""
    st.header("📊 Audit Results")

    # Health Score
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            "Health Score",
            f"{result.summary.health_score}/100",
            delta=f"Grade: {result.summary.health_grade}",
        )
    with col2:
        st.metric("Critical", result.summary.critical_count)
    with col3:
        st.metric("High", result.summary.high_count)
    with col4:
        st.metric("Medium", result.summary.medium_count)
    with col5:
        st.metric("Low", result.summary.low_count)

    st.divider()

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 Technical",
        "📝 On-Page",
        "🔗 Backlinks",
        "🏆 Competitors",
        "📥 Export"
    ])

    with tab1:
        render_issues_tab("Technical SEO", result.technical_issues, result.technical_analysis)

    with tab2:
        render_issues_tab("On-Page SEO", result.onpage_issues, result.onpage_analysis)

    with tab3:
        if result.backlink_issues:
            render_issues_tab("Backlinks", result.backlink_issues, result.backlink_analysis)
        else:
            st.info("Backlink analysis not enabled or no data available.")

    with tab4:
        if result.competitor_issues:
            render_issues_tab("Competitors", result.competitor_issues, result.competitor_analysis)
        else:
            st.info("Competitor analysis not enabled or no data available.")

    with tab5:
        render_export_tab(result)


def render_issues_tab(title: str, issues: list, analysis: str = None):
    """Render an issues tab."""
    st.subheader(f"{title} Issues ({len(issues)})")

    if not issues:
        st.info("No issues found!")
        return

    # Group by severity
    for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INSIGHT]:
        severity_issues = [i for i in issues if i.severity == severity]
        if not severity_issues:
            continue

        with st.expander(f"{severity.emoji} {severity.value.title()} ({len(severity_issues)})", expanded=severity in [Severity.CRITICAL, Severity.HIGH]):
            for issue in severity_issues:
                st.markdown(f"**{issue.title}**")
                st.markdown(f"*{issue.category.display_name}* | {issue.count} URLs affected")
                st.markdown(issue.description)
                if issue.recommendation:
                    st.markdown(f"💡 **Recommendation:** {issue.recommendation}")
                if issue.example_url:
                    st.code(issue.example_url)
                st.divider()

    # AI Analysis
    if analysis:
        st.subheader("🤖 AI Analysis")
        st.markdown(analysis)


def render_export_tab(result: AuditResult):
    """Render the export tab."""
    st.subheader("📥 Export Reports")

    generator = ReportGenerator(result)

    col1, col2, col3 = st.columns(3)

    with col1:
        # Markdown export
        md_content = generator.generate_markdown()
        st.download_button(
            "📄 Download Markdown",
            md_content,
            file_name=f"seo_audit_{result.summary.domain}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )

    with col2:
        # HTML export
        html_content = generator.generate_html()
        st.download_button(
            "🌐 Download HTML",
            html_content,
            file_name=f"seo_audit_{result.summary.domain}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
        )

    with col3:
        # CSV export
        csv_content = generator.generate_csv()
        st.download_button(
            "📊 Download CSV",
            csv_content,
            file_name=f"seo_audit_{result.summary.domain}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    # Preview
    with st.expander("Preview Markdown Report"):
        st.markdown(md_content)


def main():
    """Main application entry point."""
    init_session_state()

    # Title
    st.title("🔍 Ultimate SEO Auditor")
    st.markdown("Analyze your website with AI-powered SEO recommendations")

    # Sidebar
    options = render_sidebar()

    # Main content
    if render_upload_section():
        st.divider()

        # Competitor domains input (if enabled)
        if options.get("enable_competitors"):
            st.header("🏆 Step 2: Configure Analysis")
            competitors = st.text_input(
                "Competitor domains (optional, comma-separated)",
                placeholder="competitor1.com, competitor2.com",
                help="Leave empty to auto-discover competitors",
            )
            if competitors:
                options["competitor_domains"] = [d.strip() for d in competitors.split(",")]

        # Run Audit button
        st.divider()
        if st.button("🚀 Run SEO Audit", type="primary", use_container_width=True):
            with st.spinner("Running audit..."):
                result = run_audit(options)
                st.session_state.audit_result = result
                st.session_state.audit_complete = True

        # Show results
        if st.session_state.audit_complete and st.session_state.audit_result:
            st.divider()
            render_results(st.session_state.audit_result)

    else:
        # Instructions when no file uploaded
        st.info("""
        ### How to use:

        1. **Export from Screaming Frog**: Run a crawl and export as CSV or Excel
        2. **Upload the file**: Use the uploader above
        3. **Configure options**: Enable backlink/competitor analysis in the sidebar
        4. **Run the audit**: Click the button to analyze your data
        5. **Review & Export**: Browse issues and download reports

        **Tip**: For best results, enable GSC and PageSpeed integrations in Screaming Frog before crawling.
        """)


if __name__ == "__main__":
    main()
