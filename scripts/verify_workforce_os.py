#!/usr/bin/env python3
"""
Static validation script for Workforce OS in the LeadCurate operator dashboard.
Checks required IDs, nav, registry, project binding, page sections, relationship cards,
course builds, assets, next actions, communication feed, privacy rules, and feature preservation.
Exits with 0 on success, or 1 with failure details.
"""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DASHBOARD_PATH = os.path.join(REPO_ROOT, 'docs', 'command', 'index.html')

EXPECTED_PROJECT_ID = '0fba0555-5ef0-455d-8bed-5a518db639c0'
EXPECTED_PROJECT_SLUG = 'reentry-workforce-transition'

ORIGINAL_PAGES = [
    'hq', 'keepsakes', 'golden-crest', 'inbox', 'pipeline', 'messages',
    'workflow', 'whitelabel', 'reggie', 'templates', 'f2f-estate-sales',
    'estate-delivery', 'conference', 'marketing', 'seo', 'scout',
    'dollarleads', 'send-intake', 'send-quote', 'learn', 'tiers-ref',
    'help', 'portfolio'
]


def extract_media_blocks(css_text, max_width_pattern=r'768|640'):
    blocks = []
    for m in re.finditer(rf'@media\s*\(\s*max-width\s*:\s*(?:{max_width_pattern})px\s*\)', css_text):
        start = m.end()
        open_brace = css_text.find('{', start)
        if open_brace == -1:
            continue
        depth = 1
        pos = open_brace + 1
        while depth > 0 and pos < len(css_text):
            if css_text[pos] == '{':
                depth += 1
            elif css_text[pos] == '}':
                depth -= 1
            pos += 1
        blocks.append(css_text[open_brace + 1 : pos - 1])
    return blocks


def run_checks():
    failures = []
    passes = []

    def check(name, condition, error_msg):
        if condition:
            passes.append(name)
        else:
            failures.append(f"FAIL: {name} - {error_msg}")

    print(f"Validating Workforce OS dashboard integration in: {DASHBOARD_PATH}")

    # 1. File existence
    check(
        "File existence",
        os.path.isfile(DASHBOARD_PATH),
        f"File not found: {DASHBOARD_PATH}"
    )
    if not os.path.isfile(DASHBOARD_PATH):
        print(f"Error: {DASHBOARD_PATH} does not exist.")
        sys.exit(1)

    with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1a. Explicit favicon link pointing to existing command/icon.svg
    favicon_match = re.search(
        r'<link\s+[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\'](?:command/)?icon\.svg["\']',
        content,
        re.IGNORECASE
    ) or re.search(
        r'<link\s+[^>]*href=["\'](?:command/)?icon\.svg["\'][^>]*rel=["\'](?:shortcut )?icon["\']',
        content,
        re.IGNORECASE
    )
    check(
        "Explicit favicon link to icon.svg exists",
        bool(favicon_match),
        "docs/command/index.html missing explicit favicon link pointing to icon.svg"
    )

    # 1b. Canonical agent handoff file and AGENTS.md pointer
    start_here_path = os.path.join(REPO_ROOT, 'docs', 'workforce-os', 'START-HERE.md')
    check(
        "docs/workforce-os/START-HERE.md exists",
        os.path.isfile(start_here_path),
        f"Missing canonical agent handoff file: {start_here_path}"
    )
    if os.path.isfile(start_here_path):
        with open(start_here_path, 'r', encoding='utf-8') as sf:
            start_content = sf.read()
        check(
            "START-HERE.md states standalone live route",
            'https://leadcurate.com/workforce-os/' in start_content,
            "START-HERE.md missing standalone live route link"
        )
        check(
            "START-HERE.md states dashboard code path",
            'docs/command/index.html' in start_content,
            "START-HERE.md missing dashboard code path"
        )
        check(
            "START-HERE.md states project ID",
            EXPECTED_PROJECT_ID in start_content,
            f"START-HERE.md missing project ID {EXPECTED_PROJECT_ID}"
        )
        check(
            "START-HERE.md states VPS program source path",
            '/root/workforce-training/current' in start_content,
            "START-HERE.md missing VPS program source path"
        )
        check(
            "START-HERE.md states Dylan and Michael focus",
            'Dylan' in start_content and 'Michael' in start_content,
            "START-HERE.md missing partner focus descriptions"
        )
        check(
            "START-HERE.md specifies project_items, project_assets, activity_feed",
            'project_items' in start_content and 'project_assets' in start_content and 'activity_feed' in start_content,
            "START-HERE.md missing required table bindings"
        )
        check(
            "START-HERE.md contains no 'Day One Ready'",
            'Day One Ready' not in start_content,
            "START-HERE.md contains rejected working name 'Day One Ready'"
        )
        check(
            "START-HERE.md contains no 'Placement engine'",
            'Placement engine' not in start_content,
            "START-HERE.md contains rejected 'Placement engine' reference"
        )
        check(
            "START-HERE.md contains no 'Gaston County Reentry Council'",
            'Gaston County Reentry Council' not in start_content,
            "START-HERE.md contains unconfirmed 'Gaston County Reentry Council'"
        )

    agents_path = os.path.join(REPO_ROOT, 'AGENTS.md')
    if os.path.isfile(agents_path):
        with open(agents_path, 'r', encoding='utf-8') as af:
            agents_content = af.read()
        check(
            "AGENTS.md links to docs/workforce-os/START-HERE.md",
            'docs/workforce-os/START-HERE.md' in agents_content,
            "AGENTS.md missing pointer to docs/workforce-os/START-HERE.md"
        )

    # 2. Top-level sidebar item
    sidebar_match = re.search(
        r'<nav\s+id="sidebar"[^>]*>(.*?)</nav>', content, re.DOTALL
    )
    check("Sidebar exists", bool(sidebar_match), "nav#sidebar not found")

    if sidebar_match:
        sidebar_html = sidebar_match.group(1)
        has_nav_item = 'data-page="workforce"' in sidebar_html
        check(
            "Sidebar item data-page='workforce'",
            has_nav_item,
            "Sidebar does not have an item with data-page='workforce'"
        )

        has_workforce_label = 'Workforce OS' in sidebar_html
        check(
            "Sidebar item labeled 'Workforce OS'",
            has_workforce_label,
            "Sidebar does not contain label 'Workforce OS'"
        )

        # Ensure not inside reggie / buried under projects
        buried_in_projects = False
        reggie_match = re.search(
            r'<div\s+id="page-reggie"[^>]*>(.*?)</div>\s*<!--\s*──',
            content,
            re.DOTALL
        )
        if reggie_match and 'data-page="workforce"' in reggie_match.group(1):
            buried_in_projects = True
        check(
            "Not buried under projects",
            not buried_in_projects,
            "Workforce nav item appears buried inside page-reggie"
        )

    # 3. First-class page: page-workforce
    page_match = re.search(
        r'<div\s+id="page-workforce"\s+class="page"[^>]*>', content
    )
    check(
        "First-class page element #page-workforce exists",
        bool(page_match),
        "<div id=\"page-workforce\" class=\"page\"> not found"
    )

    # Extract page-workforce inner HTML
    page_content = ""
    page_block = re.search(
        r'<div\s+id="page-workforce"\s+class="page"[^>]*>(.*?)(?:<!--\s*──\s*INBOX|<div\s+id="page-keepsakes")',
        content,
        re.DOTALL
    )
    if page_block:
        page_content = page_block.group(1)
    else:
        page_start = content.find('id="page-workforce"')
        if page_start != -1:
            page_content = content[page_start:page_start + 25000]

    check(
        "page-workforce block extracted",
        len(page_content) > 100,
        "Could not extract page-workforce block content"
    )

    # 4. Program summary section
    has_program_summary = (
        'wf-summary-title' in page_content or
        'Workforce Training &amp; Reentry Career Systems' in page_content or
        'Workforce Training & Reentry Career Systems' in page_content or
        'PROGRAM DOCTRINE' in page_content
    )
    check(
        "Current program summary section exists",
        has_program_summary,
        "Program summary section missing in page-workforce"
    )

    # Check positioning facts
    check(
        "Positioning: Sales Career Instructor",
        'Sales Career Instructor' in content,
        "Derrick positioning as Sales Career Instructor missing"
    )
    check(
        "Positioning: AI Operator & Product Builder",
        'AI Operator & Product Builder' in content or 'AI Operator &amp; Product Builder' in content,
        "Derrick positioning as AI Operator & Product Builder missing"
    )

    # 5. Relationship cards: Dylan Lehr & Michael S. Coone
    check(
        "Dylan Lehr relationship reference",
        'Dylan Lehr' in content,
        "Dylan Lehr relationship card missing"
    )
    check(
        "Dylan Lehr: Two Hawk / NCWorks",
        'Two Hawk' in content and 'NCWorks' in content,
        "Dylan Lehr organization details (Two Hawk / NCWorks) missing"
    )
    check(
        "Dylan Lehr: Sales-course-first",
        'Sales-Course-First' in content or 'sales-course-first' in content,
        "Dylan Lehr sales-course-first focus missing"
    )
    check(
        "Michael S. Coone relationship reference",
        'Michael S. Coone' in content or 'Michael Coone' in content,
        "Michael S. Coone relationship card missing"
    )
    check(
        "Michael S. Coone: Gaston workforce board / WIOA / reentry",
        'Gaston' in content and ('Workforce Development Board' in content or 'WIOA' in content),
        "Michael S. Coone board / WIOA details missing"
    )

    # 6. Future relationship support via Supabase project_items (not localStorage)
    check(
        "Dynamic relationship support functions exist",
        'getWorkforceRelationships' in content and 'saveWorkforcePartner' in content,
        "Dynamic relationship partner functions missing"
    )

    # 6a. Specifically fail if unsupported '0M' text exists
    check(
        "No unsupported '0M' claims exist",
        '0M' not in content,
        "Found unsupported '0M' text claim in dashboard content"
    )
    check(
        "No unsupported 'elite sales career' claim",
        'elite sales career' not in content.lower(),
        "Found unsupported 'elite sales career' text in dashboard content"
    )
    check(
        "No rejected 'Day One Ready' in docs/command/index.html",
        'Day One Ready' not in content,
        "Found rejected 'Day One Ready' reference in docs/command/index.html"
    )
    check(
        "No 'Placement engine' claim in docs/command/index.html",
        'Placement engine' not in content,
        "Found 'Placement engine' claim in docs/command/index.html"
    )
    check(
        "No unconfirmed 'Gaston County Reentry Council' in docs/command/index.html",
        'Gaston County Reentry Council' not in content,
        "Found unconfirmed 'Gaston County Reentry Council' reference in docs/command/index.html"
    )

    # 6b. Specifically fail if workforce relationship saving uses localStorage
    save_partner_match = re.search(
        r'(?:window\.)?saveWorkforcePartner\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{(.*?)\n\};',
        content,
        re.DOTALL
    )
    save_partner_body = save_partner_match.group(1) if save_partner_match else ""
    check(
        "saveWorkforcePartner function found",
        bool(save_partner_body),
        "Could not extract saveWorkforcePartner function body"
    )
    check(
        "Workforce relationship saving does not use localStorage",
        'localStorage' not in save_partner_body and 'lc.workforce.relationships' not in content,
        "Workforce relationship saving uses localStorage instead of Supabase"
    )

    # 6c. Specifically fail if saveWorkforcePartner does not write a project_items row with project_id
    writes_project_items = (
        'project_items' in save_partner_body and
        ('project_id' in save_partner_body or 'WORKFORCE_PROJECT_ID' in save_partner_body) and
        ("kind: 'relationship'" in save_partner_body or 'kind:"relationship"' in save_partner_body)
    )
    check(
        "saveWorkforcePartner writes project_items row with project_id",
        writes_project_items,
        "saveWorkforcePartner does not write a project_items row with project_id and kind='relationship'"
    )

    # 6d. getWorkforceRelationships must source from Supabase project_items
    get_rel_match = re.search(
        r'function\s+getWorkforceRelationships\s*\([^)]*\)\s*\{(.*?)\n\}',
        content,
        re.DOTALL
    )
    get_rel_body = get_rel_match.group(1) if get_rel_match else ""
    reads_project_items_rel = (
        'PROJECT_ITEMS' in get_rel_body and
        ('relationship' in get_rel_body) and
        ('kind' in get_rel_body) and
        'localStorage' not in get_rel_body
    )
    check(
        "getWorkforceRelationships sources from project_items",
        reads_project_items_rel,
        "getWorkforceRelationships does not read from PROJECT_ITEMS with kind='relationship' or uses localStorage"
    )

    # 6e. Specifically fail if page=workforce deep-link parsing is absent
    has_deeplink_parsing = (
        'URLSearchParams' in content and
        ('page' in content) and
        ('get(\'page\')' in content or 'get("page")' in content or 'page=workforce' in content) and
        ('replaceState' in content or 'pushState' in content)
    )
    check(
        "page=workforce deep-link parsing is present",
        has_deeplink_parsing,
        "page=workforce deep-link parsing is absent"
    )

    # 6f. Fallback project label must be 'Workforce OS'
    check(
        "Fallback project label is 'Workforce OS'",
        'Workforce OS (Reentry Workforce Transition)' not in content,
        "Found deprecated fallback project label 'Workforce OS (Reentry Workforce Transition)'"
    )

    # 7. Courses and build status
    check(
        "Sales course: 4 modules / 8 sessions",
        ('4 Modules' in content or '4 modules' in content) and
        ('8 Sessions' in content or '8 sessions' in content),
        "Sales course 4 modules / 8 sessions structure missing"
    )
    check(
        "Business course: 7 sessions",
        '7 Sessions' in content or '7 sessions' in content or 'seven sessions' in content.lower(),
        "Business course 7 sessions structure missing"
    )
    check(
        "Applied AI embedded in courses",
        'Applied AI Embedded' in content or 'applied AI' in content.lower(),
        "Applied AI embedded designation missing"
    )

    # 8. Document / visual / portal / product asset area
    check(
        "Workforce assets container exists",
        'id="wf-assets-list"' in page_content,
        "id='wf-assets-list' missing from page-workforce"
    )
    check(
        "Workforce asset form exists",
        'id="wf-asset-form"' in page_content,
        "id='wf-asset-form' missing from page-workforce"
    )
    check(
        "Asset rendering function exists",
        'renderWorkforceAssets' in content,
        "renderWorkforceAssets function missing"
    )

    # 9. Next actions driven from project items
    check(
        "Next actions container exists",
        'id="wf-items-list"' in page_content,
        "id='wf-items-list' missing from page-workforce"
    )
    check(
        "Next actions form exists",
        'id="wf-item-form"' in page_content,
        "id='wf-item-form' missing from page-workforce"
    )
    check(
        "Item rendering function exists",
        'renderWorkforceItems' in content,
        "renderWorkforceItems function missing"
    )

    # 10. Project-specific activity / communication feed
    check(
        "Workforce activity container exists",
        'id="wf-activity-list"' in page_content,
        "id='wf-activity-list' missing from page-workforce"
    )
    check(
        "Communication form message body exists",
        'id="wf-comm-body"' in page_content,
        "id='wf-comm-body' missing from page-workforce"
    )
    check(
        "Communication form submit handler exists",
        'saveWorkforceCommunication' in content,
        "saveWorkforceCommunication function missing"
    )
    check(
        "Communication form post button exists",
        'id="wf-comm-save"' in page_content,
        "id='wf-comm-save' missing from page-workforce"
    )

    # 10a. Workforce OS must stay independent from the generic Projects UI
    check(
        "Workforce OS has no Projects Workspace escape hatch",
        'Projects Workspace' not in page_content and 'window.openProject(' not in page_content,
        "Workforce OS still contains a Projects Workspace button or openProject path"
    )

    # 10b. Conference Room must query its own messages and render targets safely
    render_conf_match = re.search(
        r'async function\s+renderConference\s*\([^)]*\)\s*\{(.*?)\n\}',
        content,
        re.DOTALL
    )
    render_conf_body = render_conf_match.group(1) if render_conf_match else ""
    check(
        "Conference Room renderer has a dedicated Supabase conf query",
        "activity_feed" in render_conf_body and "conf:%" in render_conf_body,
        "renderConference relies only on the generic FEED cache"
    )
    check(
        "Conference Room defines target label before rendering",
        'const toLabel' in render_conf_body,
        "renderConference references toLabel without defining it"
    )
    check(
        "Conference Room navigation awaits rendering",
        "await renderConference" in content,
        "Conference Room navigation does not await its data-backed renderer"
    )

    # 11. JS pages registry and navigation flow
    pages_match = re.search(r"const\s+pages\s*=\s*\[(.*?)\];", content)
    check("JS pages array exists", bool(pages_match), "const pages = [...] array not found")
    if pages_match:
        pages_str = pages_match.group(1)
        check(
            "workforce in pages registry",
            "'workforce'" in pages_str or '"workforce"' in pages_str,
            "'workforce' not found in pages array"
        )

    check(
        "window.nav routing for workforce",
        "id==='workforce'" in content or 'id === "workforce"' in content or "id === 'workforce'" in content,
        "window.nav does not handle id==='workforce'"
    )

    check(
        "Conference room workforce project link navigates to workforce",
        ('WORKFORCE_PROJECT_ID' in content and ("nav('workforce')" in content or 'nav(\\\'workforce\\\')' in content)),
        "Conference room project link does not navigate to workforce"
    )

    # 12. Supabase project binding
    check(
        f"Project ID binding ({EXPECTED_PROJECT_ID})",
        EXPECTED_PROJECT_ID in content,
        f"Project ID {EXPECTED_PROJECT_ID} missing in code"
    )
    check(
        f"Project slug binding ({EXPECTED_PROJECT_SLUG})",
        EXPECTED_PROJECT_SLUG in content,
        f"Project slug {EXPECTED_PROJECT_SLUG} missing in code"
    )

    # 13. Privacy & security audit
    raw_vps_hrefs = re.findall(
        r'href=["\'](?:/root/|/opt/|file:///root/|file:///opt/)[^"\']*["\']',
        page_content
    )
    check(
        "No private VPS href paths in page-workforce",
        len(raw_vps_hrefs) == 0,
        f"Found private VPS paths in href attributes: {raw_vps_hrefs}"
    )

    check(
        "Asset path sanitization function present",
        'sanitizeAssetNotes' in content,
        "sanitizeAssetNotes helper missing"
    )

    # 14. Preserve all original pages
    for p in ORIGINAL_PAGES:
        check(
            f"Original page preserved in registry: {p}",
            f"'{p}'" in (pages_str if pages_match else ""),
            f"Page '{p}' was removed from pages registry"
        )
        check(
            f"Original page DOM exists: page-{p}",
            f'id="page-{p}"' in content,
            f"DOM element id='page-{p}' was removed"
        )

    # 15. Mobile containment rules under max-width 768 / 640
    mobile_blocks = extract_media_blocks(content)
    wf_mobile_blocks = [b for b in mobile_blocks if '#page-workforce' in b or '.wf-' in b]
    mobile_css = "\n".join(wf_mobile_blocks)
    check(
        "Mobile media query block for Workforce OS exists",
        len(wf_mobile_blocks) > 0,
        "No mobile media query block found for Workforce OS under max-width 768px or 640px"
    )

    # 15a. Cards and grid children use min-width: 0
    has_min_width_zero = (
        'min-width:0' in mobile_css.replace(' ', '') and
        ('.wf-grid-2' in mobile_css or '#page-workforce' in mobile_css)
    )
    check(
        "Mobile containment: cards and grid children use min-width: 0",
        has_min_width_zero,
        "Mobile CSS missing min-width: 0 for cards/grid children under #page-workforce"
    )

    # 15b. Text wraps with overflow-wrap: anywhere
    has_overflow_wrap = (
        'overflow-wrap:anywhere' in mobile_css.replace(' ', '') or
        'overflow-wrap: anywhere' in mobile_css
    )
    check(
        "Mobile containment: text wraps with overflow-wrap: anywhere",
        has_overflow_wrap,
        "Mobile CSS missing overflow-wrap: anywhere for #page-workforce text elements"
    )

    # 15c. Heading and subtitle width max 100%
    has_heading_sub_max_width = (
        '.page-title' in mobile_css and
        '.page-sub' in mobile_css and
        ('max-width:100%' in mobile_css.replace(' ', '') or 'max-width: 100%' in mobile_css)
    )
    check(
        "Mobile containment: heading/subtitle max-width 100%",
        has_heading_sub_max_width,
        "Mobile CSS missing max-width: 100% for #page-workforce .page-title and .page-sub"
    )

    # 15d. Forms and controls fit
    has_forms_fit = (
        ('f-input' in mobile_css or 'project-form' in mobile_css or 'wf-comm-box' in mobile_css) and
        ('100%' in mobile_css) and
        ('box-sizing' in mobile_css)
    )
    check(
        "Mobile containment: forms and controls fit",
        has_forms_fit,
        "Mobile CSS missing form and control containment rules"
    )

    # 15e. Grids collapse to 1fr
    has_grid_collapse = (
        '.wf-grid-2' in mobile_css and
        'grid-template-columns:1fr' in mobile_css.replace(' ', '')
    )
    check(
        "Mobile containment: grids collapse to 1fr",
        has_grid_collapse,
        "Mobile CSS missing 1fr collapse for .wf-grid-2"
    )

    # 15f. No content is hidden on mobile
    bad_hide_match = re.search(
        r'#page-workforce\s+(?:.page-title|.page-sub|.card|.wf-card|.wf-summary-card|#wf-stats)\s*\{[^}]*display\s*:\s*none',
        mobile_css
    )
    check(
        "Mobile containment: no content is hidden",
        not bool(bad_hide_match),
        f"Found illegal display:none hiding workforce content on mobile: {bad_hide_match.group(0) if bad_hide_match else ''}"
    )

    # 16. Summary of test results
    print("\n--- TEST SUMMARY ---")
    print(f"Total checks: {len(passes) + len(failures)}")
    print(f"Passed: {len(passes)}")
    print(f"Failed: {len(failures)}")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")
        return False

    print("\nAll Workforce OS static checks PASSED successfully.")
    return True


if __name__ == '__main__':
    ok = run_checks()
    sys.exit(0 if ok else 1)
