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
from utils.audit_context import AuditContext, load_audit_context
from models.audit_result import AuditResult, AuditSummary, Severity
from auditors.technical_auditor import TechnicalAuditor
from auditors.javascript_rendering_auditor import JavaScriptRenderingAuditor
from auditors.cannibalization_auditor import CannibalizationAuditor
from auditors.url_structure_auditor import URLStructureAuditor
from auditors.ecommerce_patterns_auditor import EcommercePatternsAuditor
from auditors.local_seo_auditor import LocalSEOAuditor
from auditors.mobile_first_auditor import MobileFirstAuditor
from auditors.content_pruning_auditor import ContentPruningAuditor
from auditors.onpage_auditor import OnPageAuditor
from auditors.backlink_auditor import BacklinkAuditor
from auditors.competitor_auditor import CompetitorAuditor
# Leak-grounded auditors (May 2024 Google API leak inputs)
from auditors.anchor_quality_auditor import AnchorQualityAuditor
from auditors.date_freshness_auditor import DateFreshnessAuditor
from auditors.topical_authority_auditor import TopicalAuthorityAuditor
from auditors.click_signal_auditor import ClickSignalAuditor
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
        # Leak-grounded expanded input stack
        "audit_context": None,
        "backlinks_df": None,
        "anchors_df": None,
        "dates_df": None,
        "gsc_df": None,
        "topical_map": None,
        # Computed semantic map (from run_semantic_map.py)
        "computed_topical_path": None,
        "computed_full_path": None,
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
    """Render the expanded 6-input upload section.

    Inputs (1 required, 5 optional but recommended for full leak-grounded audit):
        1. SF HTML Internal report      — REQUIRED — core crawl
        2. SEMrush backlink report      — backlink quality + domain authority
        3. SF Anchor Text report        — anchor mismatch + spam velocity
        4. SF custom extraction (dates) — date triangulation
        5. GSC Search Analytics export  — position-adjusted CTR + click signals
        6. Koray topical map (markdown) — siteFocusScore / siteRadius proxy
    """
    st.header("📁 Step 1: Upload Audit Inputs")
    st.caption(
        "Only the SF Internal report is required. Each additional input unlocks "
        "leak-grounded analyses (May 2024 Google API leak)."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Required**")
        crawl_file = st.file_uploader(
            "1. SF HTML Internal report",
            type=["csv", "xlsx", "xls"],
            key="upload_crawl",
            help="Screaming Frog export. Standard Internal HTML crawl.",
        )

        st.markdown("**Recommended — leak-grounded**")
        anchors_file = st.file_uploader(
            "3. SF Anchor Text report",
            type=["csv", "xlsx", "xls"],
            key="upload_anchors",
            help="SF Bulk Export → All Anchor Text. Unlocks anchorMismatchDemotion + phraseAnchorSpam analysis.",
        )

        gsc_file = st.file_uploader(
            "5. GSC Search Analytics export",
            type=["csv", "xlsx", "xls"],
            key="upload_gsc",
            help="GSC Performance → Export with query + page dimensions. Unlocks position-adjusted CTR analysis.",
        )

    with col_b:
        st.markdown("**Optional**")
        backlinks_file = st.file_uploader(
            "2. SEMrush backlink report",
            type=["csv", "xlsx", "xls"],
            key="upload_backlinks",
            help="SEMrush Backlink export. Unlocks external authority + sourceType tier analysis.",
        )

        dates_file = st.file_uploader(
            "4. SF content dates extraction",
            type=["csv", "xlsx", "xls"],
            key="upload_dates",
            help="SF custom extraction with byline / schema published+modified / Last-Modified. Unlocks date triangulation.",
        )

        topical_file = st.file_uploader(
            "6. Topical map (Koray-style)",
            type=["md", "markdown", "txt"],
            key="upload_topical",
            help="Markdown file with central entity, Ring 1/2/3 topics, outliers. Unlocks siteFocusScore / siteRadius analysis.",
        )

        computed_map_file = st.file_uploader(
            "7. Computed semantic map (optional, JSON)",
            type=["json"],
            key="upload_computed_map",
            help=(
                "Output of `python run_semantic_map.py --client <name>` "
                "(topical_map.json). Use this when the client does not "
                "have a Koray topical map - the skill generates one from "
                "the SF crawl + embeddings. Pair with the full JSON below "
                "for the click-overlay finding."
            ),
        )

        full_map_file = st.file_uploader(
            "8. Semantic map full JSON (optional)",
            type=["json"],
            key="upload_full_map",
            help=(
                "Optional richer payload (semantic_map_full.json) that "
                "unlocks the high-click off-topic cluster finding."
            ),
        )

    if not crawl_file:
        st.info("Upload at least the SF HTML Internal report to begin.")
        return False

    with st.spinner("Parsing audit inputs..."):
        try:
            ctx = load_audit_context(
                crawl_file=crawl_file,
                backlinks_file=backlinks_file,
                anchors_file=anchors_file,
                dates_file=dates_file,
                gsc_file=gsc_file,
                topical_map_file=topical_file,
            )

            if ctx.crawl_df is None:
                st.error("Failed to parse the SF Internal report.")
                return False

            df = ctx.crawl_df
            st.session_state.df = df
            st.session_state.audit_context = ctx
            st.session_state.domain = ctx.domain
            st.session_state.integrations = ctx.integrations
            st.session_state.backlinks_df = ctx.backlinks_df
            st.session_state.anchors_df = ctx.anchors_df
            st.session_state.dates_df = ctx.dates_df
            st.session_state.gsc_df = ctx.gsc_df
            st.session_state.topical_map = ctx.topical_map

            # Persist optional computed-map uploads to temp paths so the
            # auditor (which expects file paths) can consume them later.
            st.session_state.computed_topical_path = None
            st.session_state.computed_full_path = None
            if computed_map_file is not None:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    suffix=".json", delete=False, mode="wb"
                ) as tf:
                    tf.write(computed_map_file.getvalue())
                    st.session_state.computed_topical_path = tf.name
            if full_map_file is not None:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    suffix=".json", delete=False, mode="wb"
                ) as tf:
                    tf.write(full_map_file.getvalue())
                    st.session_state.computed_full_path = tf.name

            st.success(f"✓ Loaded {len(df):,} URLs from {ctx.domain or 'Unknown domain'}")

            _render_input_availability(ctx)
            _render_crawl_diagnostics(df)

        except Exception as e:
            st.error(f"Error parsing inputs: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.df = None

    return st.session_state.df is not None


def _render_input_availability(ctx: AuditContext) -> None:
    """Render the availability matrix for the 6 inputs and the analyses they unlock."""
    inputs = ctx.available_inputs
    analyses = ctx.available_analyses

    st.markdown("### 📊 Input Availability")
    cols = st.columns(6)
    labels = [
        ("Crawl", "crawl"),
        ("Backlinks", "backlinks"),
        ("Anchors", "anchors"),
        ("Dates", "dates"),
        ("GSC", "gsc"),
        ("Topical Map", "topical_map"),
    ]
    for col, (label, key) in zip(cols, labels):
        with col:
            mark = "✅" if inputs[key] else "⚪"
            st.metric(label, mark)

    with st.expander("🔬 Leak-grounded analyses unlocked by current inputs"):
        analysis_labels = {
            "anchor_mismatch_demotion": "Anchor mismatch demotion (CompressedQualitySignals)",
            "anchor_spam_velocity": "Anchor phrase spam velocity (AnchorPhraseSpamInfo)",
            "external_backlink_quality": "External backlink quality (Anchors sourceType)",
            "site_authority_signal": "Site authority (NSR siteAuthority proxy)",
            "date_triangulation": "Date triangulation (semanticDate / lastSignificantUpdate)",
            "freshness_unreliability": "Freshness unreliability (dateUnreliabilityInfo)",
            "position_adjusted_ctr": "Position-adjusted CTR (NavBoost goodClicks)",
            "click_signal_grounding": "Click-signal grounding (NavBoost / Glue)",
            "topical_authority_outliers": "Topical outliers (siteRadius)",
            "site_radius_analysis": "Site focus / radius (QualityAuthorityTopicEmbeddings)",
        }
        for analysis_key, label in analysis_labels.items():
            mark = "✅" if analyses.get(analysis_key) else "⛔"
            st.markdown(f"- {mark} {label}")


def _render_crawl_diagnostics(df: pd.DataFrame) -> None:
    """Render the existing crawl summary metrics + column diagnostics expander."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total URLs", f"{len(df):,}")
    with col2:
        st.metric("Columns", f"{len(df.columns)}")
    with col3:
        gsc = "Yes" if st.session_state.integrations.get("gsc") else "No"
        st.metric("GSC Crawl Data", gsc)
    with col4:
        ps = "Yes" if st.session_state.integrations.get("pagespeed") else "No"
        st.metric("PageSpeed Data", ps)

    with st.expander("Preview Data"):
        st.dataframe(df.head(10), use_container_width=True)

    with st.expander("🔧 Column Diagnostics (Debug)"):
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
                    non_null_vals = df[std_name].dropna()
                    sample = str(non_null_vals.iloc[0])[:50] if len(non_null_vals) > 0 else "empty"
            status = "✅" if exists and has_data else "❌" if not exists else "⚠️ (empty)"
            col_status.append(f"- {display_name} (`{std_name}`): {status} - Sample: `{sample}`")
        st.markdown("\n".join(col_status))

        st.markdown(f"\n**All {len(df.columns)} columns in file:**")
        st.code(", ".join(df.columns.tolist()))


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
    progress.progress(20)

    # JavaScript Rendering Audit (gracefully degrades when render data absent)
    status.text("Running JavaScript rendering audit...")
    js_auditor = JavaScriptRenderingAuditor(df)
    result.technical_issues.extend(js_auditor.run_audit())
    progress.progress(25)

    # URL Structure Audit
    status.text("Running URL structure audit...")
    url_auditor = URLStructureAuditor(df)
    result.technical_issues.extend(url_auditor.run_audit())
    progress.progress(30)

    # Cannibalization Audit
    status.text("Running cannibalization audit...")
    cannibal_auditor = CannibalizationAuditor(df)
    result.technical_issues.extend(cannibal_auditor.run_audit())
    progress.progress(35)

    # Mobile-First Audit
    status.text("Running mobile-first audit...")
    mobile_auditor = MobileFirstAuditor(df)
    result.technical_issues.extend(mobile_auditor.run_audit())
    progress.progress(38)

    # Ecommerce Patterns Audit (gates on site-type detection)
    status.text("Running ecommerce patterns audit...")
    ecom_auditor = EcommercePatternsAuditor(df)
    result.technical_issues.extend(ecom_auditor.run_audit())
    progress.progress(42)

    # Local SEO Audit (gates on site-type detection)
    status.text("Running local SEO audit...")
    local_auditor = LocalSEOAuditor(df)
    result.technical_issues.extend(local_auditor.run_audit())
    progress.progress(45)

    # On-Page Audit
    status.text("Running on-page SEO audit...")
    onpage_auditor = OnPageAuditor(df)
    result.onpage_issues = onpage_auditor.run_audit()
    progress.progress(48)

    # Content Pruning Audit (on-page concern)
    status.text("Running content pruning audit...")
    pruning_auditor = ContentPruningAuditor(df)
    result.onpage_issues.extend(pruning_auditor.run_audit())
    progress.progress(50)

    # ==== Leak-grounded auditors (gracefully skip when inputs absent) ====
    ctx = st.session_state.get("audit_context")
    if ctx is not None:
        # Anchor Quality Audit (requires SF Anchor Text report)
        if ctx.anchors_df is not None:
            status.text("Running anchor quality audit (anchorMismatchDemotion + spam velocity)...")
            try:
                aq_auditor = AnchorQualityAuditor(df, ctx.anchors_df)
                result.onpage_issues.extend(aq_auditor.run_audit())
            except Exception as e:
                st.warning(f"Anchor quality audit failed: {e}")
        progress.progress(54)

        # Date Freshness Audit (requires custom dates extraction)
        if ctx.dates_df is not None:
            status.text("Running date triangulation audit (semanticDate / lastSignificantUpdate)...")
            try:
                df_auditor = DateFreshnessAuditor(df, ctx.dates_df)
                result.onpage_issues.extend(df_auditor.run_audit())
            except Exception as e:
                st.warning(f"Date freshness audit failed: {e}")
        progress.progress(58)

        # Topical Authority Audit
        # Prefer a computed semantic map (from run_semantic_map.py) when
        # uploaded; fall back to the Koray topical map otherwise.
        computed_topical = st.session_state.get(
            "computed_topical_path"
        )
        computed_full = st.session_state.get("computed_full_path")
        if computed_topical is not None:
            status.text(
                "Running topical authority audit "
                "(computed semantic map)..."
            )
            try:
                ta_auditor = (
                    TopicalAuthorityAuditor.from_computed_map(
                        crawl_df=df,
                        topical_map_path=computed_topical,
                        full_json_path=computed_full,
                    )
                )
                result.onpage_issues.extend(ta_auditor.run_audit())
            except Exception as e:
                st.warning(f"Topical authority audit failed: {e}")
        elif ctx.topical_map is not None:
            status.text(
                "Running topical authority audit "
                "(siteRadius / siteFocusScore)..."
            )
            try:
                ta_auditor = TopicalAuthorityAuditor(
                    df, ctx.topical_map
                )
                result.onpage_issues.extend(ta_auditor.run_audit())
            except Exception as e:
                st.warning(f"Topical authority audit failed: {e}")
        progress.progress(62)

        # Click Signal Audit (requires GSC performance export)
        if ctx.gsc_df is not None:
            status.text("Running click-signal audit (position-adjusted CTR / NavBoost)...")
            try:
                cs_auditor = ClickSignalAuditor(df, ctx.gsc_df)
                result.onpage_issues.extend(cs_auditor.run_audit())
            except Exception as e:
                st.warning(f"Click signal audit failed: {e}")
        progress.progress(66)
    # ====================================================================

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
