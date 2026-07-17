/**
 * GitFlare Web UI — vanilla JS SPA with GitHub/GitLab style toggle
 */

const app = document.getElementById('app');
const sidebarNav = document.getElementById('sidebar-nav');

// --- Style management ---

function getStyle() {
    return localStorage.getItem('gitflare-style') || 'gitlab';
}

function renderTopBar() {
    // Remove existing top bar
    const existing = document.querySelector('.top-bar');
    if (existing) existing.remove();

    if (getStyle() !== 'github') return;

    const bar = document.createElement('header');
    bar.className = 'top-bar';
    const isGithub = getStyle() === 'github';
    bar.innerHTML = `
        <a href="/" class="top-bar-brand">
            <div class="top-bar-logo">
                <span class="material-symbols-outlined">local_fire_department</span>
            </div>
            <span class="top-bar-title">GitFlare</span>
        </a>
        <nav class="top-bar-nav">
            <a href="/" class="active">Repositories</a>
            <a href="/health" target="_blank">Health</a>
            <a href="https://github.com/SabeeirSharrma/GitFlare" target="_blank">Source</a>
        </nav>
        <div class="top-bar-actions">
            <a href="/ui/api/repos" target="_blank">
                <span class="material-symbols-outlined">api</span>
                API
            </a>
            <button onclick="toggleStyle()">
                <span class="material-symbols-outlined">${isGithub ? 'view_sidebar' : 'web'}</span>
                ${isGithub ? 'GitLab Style' : 'GitHub Style'}
            </button>
        </div>
    `;
    document.querySelector('.app-layout').prepend(bar);
}

function toggleStyle() {
    const next = getStyle() === 'github' ? 'gitlab' : 'github';
    localStorage.setItem('gitflare-style', next);
    document.body.className = `style-${next}`;
    renderTopBar();
    updateSidebarToggle();
    handleRoute();
}

function updateSidebarToggle() {
    const btn = document.getElementById('style-toggle-btn');
    if (!btn) return;
    const isGithub = getStyle() === 'github';
    btn.innerHTML = `
        <span class="material-symbols-outlined">${isGithub ? 'view_sidebar' : 'web'}</span>
        <span>${isGithub ? 'GitLab Style' : 'GitHub Style'}</span>
    `;
}

// Initialize style
document.body.className = `style-${getStyle()}`;
renderTopBar();

// Add style switch button to sidebar
if (sidebarNav) {
    const btn = document.createElement('button');
    btn.id = 'style-toggle-btn';
    btn.className = 'sidebar-item';
    btn.onclick = toggleStyle;
    btn.style.cssText = 'width:100%;border:none;background:none;cursor:pointer;font-family:inherit;text-align:left;';
    sidebarNav.appendChild(btn);
    updateSidebarToggle();
}

// --- Router ---

function getRoute() {
    const hash = window.location.hash.slice(1) || '/';
    return hash;
}

function navigate(path) {
    window.location.hash = path;
}

// --- API ---

async function api(path) {
    const res = await fetch(`/ui/api${path}`);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
}

// --- Helpers ---

function esc(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function timeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 2592000) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// --- Renderers ---

async function renderRepoList() {
    try {
        const repos = await api('/repos');

        if (repos.length === 0) {
            app.innerHTML = `
                <div class="page-container">
                    <div class="empty-state">
                        <p>No repositories yet.</p>
                        <p>Create one with <code>gitflare-admin repo create &lt;name&gt;</code></p>
                    </div>
                </div>
            `;
            return;
        }

        const cards = repos.map(r => {
            const latest = r.latest_commit
                ? `<div class="repo-card-latest">
                        <span class="commit-hash">${esc(r.latest_commit.hash.slice(0, 7))}</span>
                        <span class="commit-msg">${esc(r.latest_commit.message)}</span>
                        <span class="commit-meta">${esc(r.latest_commit.author)} · ${timeAgo(r.latest_commit.date)}</span>
                   </div>`
                : '';

            return `
                <div class="repo-card" onclick="navigate('#/${esc(r.name)}')">
                    <div class="repo-card-header">
                        <div class="repo-card-name">
                            <span class="material-symbols-outlined">book</span>
                            <a href="#/${esc(r.name)}">${esc(r.name)}</a>
                        </div>
                        <span class="auth-badge">${esc(r.auth_mode)}</span>
                    </div>
                    <div class="repo-card-meta">
                        <span>${r.branch_count} branch${r.branch_count !== 1 ? 'es' : ''}</span>
                    </div>
                    ${latest}
                </div>
            `;
        }).join('');

        app.innerHTML = `
            <div class="page-container">
                <div class="page-header">
                    <h2>Repositories</h2>
                    <span class="count">${repos.length} total</span>
                </div>
                <div class="repo-grid">${cards}</div>
            </div>
        `;
    } catch (err) {
        app.innerHTML = `<div class="page-container"><div class="error">Failed to load repositories: ${esc(err.message)}</div></div>`;
    }
}

async function renderRepoDetail(name) {
    try {
        const info = await api(`/repos/${name}`);
        const defaultBranch = info.default_branch;

        // Stats
        const totalCommits = info.commits.length;

        // File explorer
        let fileItems = '';
        try {
            const tree = await api(`/repos/${name}/tree/${defaultBranch}`);
            fileItems = tree.items.map(item => {
                const icon = item.type === 'dir' ? 'folder' : 'description';
                const iconClass = item.type === 'dir' ? 'dir' : 'file';
                const itemPath = item.name;
                const href = item.type === 'dir'
                    ? `#/${esc(name)}/tree/${esc(defaultBranch)}/${esc(itemPath)}`
                    : `#/${esc(name)}/blob/${esc(defaultBranch)}/${esc(itemPath)}`;

                const commitInfo = item.last_commit
                    ? `<div class="file-commit-msg">${esc(item.last_commit.message)}</div>
                       <div class="file-date">${timeAgo(item.last_commit.date)}</div>`
                    : `<div class="file-commit-msg"></div><div class="file-date"></div>`;

                return `
                    <div class="file-item" onclick="window.location.href='${href}'">
                        <div class="file-icon ${iconClass}">
                            <span class="material-symbols-outlined">${icon}</span>
                        </div>
                        <div class="file-name"><a href="${href}">${esc(item.name)}</a></div>
                        ${commitInfo}
                    </div>
                `;
            }).join('');
        } catch (e) {
            fileItems = '<div class="empty-state">Empty repository</div>';
        }

        // README
        let readmeContent = '';
        try {
            const blob = await api(`/repos/${name}/blob/${defaultBranch}/README.md`);
            if (!blob.binary) {
                const rendered = typeof marked !== 'undefined'
                    ? marked.parse(blob.content)
                    : `<pre>${esc(blob.content)}</pre>`;
                readmeContent = `
                    <div class="file-explorer" style="margin-top: var(--space-md)">
                        <div class="file-explorer-header">
                            <div class="commit-info">
                                <span class="material-symbols-outlined" style="font-size:16px">article</span>
                                <strong>README.md</strong>
                            </div>
                        </div>
                        <div class="markdown-body">${rendered}</div>
                    </div>
                `;
            }
        } catch (e) {
            // No README, that's fine
        }

        // Commits for sidebar
        const commitsHtml = info.commits.slice(0, 5).map(c => `
            <div class="commit-item">
                <div class="commit-message">${esc(c.message)}</div>
                <div class="commit-meta">
                    <span class="commit-hash">${esc(c.hash.slice(0, 7))}</span>
                    <span>${esc(c.author)}</span>
                    <span>${timeAgo(c.date)}</span>
                </div>
            </div>
        `).join('');

        // Branches for sidebar
        const branchesHtml = info.branches.map(b => `
            <div class="ref-item">
                <span class="ref-name ${b === defaultBranch ? 'default' : ''}">
                    <a href="#/${esc(name)}/tree/${esc(b)}">${esc(b)}</a>
                    ${b === defaultBranch ? ' (default)' : ''}
                </span>
            </div>
        `).join('');

        // Tags for sidebar
        const tagsHtml = info.tags.length > 0
            ? info.tags.map(t => `
                <div class="ref-item">
                    <span class="ref-name">${esc(t.name)}</span>
                    <span class="ref-hash">${esc(t.commit)}</span>
                </div>
            `).join('')
            : '<div style="font-size:13px;color:var(--on-surface-variant)">No tags</div>';

        app.innerHTML = `
            <div class="page-container">
                <div class="repo-header">
                    <div class="repo-header-top">
                        <div class="repo-header-title">
                            <span class="material-symbols-outlined">book</span>
                            <a href="#/${esc(name)}">${esc(name)}</a>
                            <span class="auth-badge">${esc(info.auth_mode)}</span>
                        </div>
                    </div>
                    <div class="clone-box">
                        <label>Clone:</label>
                        <input class="clone-url" type="text" readonly
                               value="${esc(name)}.git"
                               onclick="this.select()">
                        <button class="btn btn-secondary" onclick="navigator.clipboard.writeText('${esc(name)}.git')">
                            <span class="material-symbols-outlined">content_copy</span>
                            Copy
                        </button>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Commits</div>
                        <div class="stat-value">${totalCommits}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Branches</div>
                        <div class="stat-value">${info.branches.length}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Tags</div>
                        <div class="stat-value">${info.tags.length}</div>
                    </div>
                </div>

                <div class="content-grid">
                    <div>
                        <div class="file-explorer">
                            <div class="file-explorer-header">
                                <div class="commit-info">
                                    <span class="material-symbols-outlined" style="font-size:16px">account_tree</span>
                                    <strong>${esc(defaultBranch)}</strong>
                                </div>
                            </div>
                            <ul class="file-list">
                                ${fileItems}
                            </ul>
                        </div>
                        ${readmeContent}
                    </div>
                    <div>
                        <div class="sidebar-panel">
                            <div class="sidebar-panel-title">
                                Branches
                                <span class="count">${info.branches.length}</span>
                            </div>
                            <div class="ref-list">${branchesHtml}</div>
                        </div>
                        <div class="sidebar-panel">
                            <div class="sidebar-panel-title">
                                Tags
                                <span class="count">${info.tags.length}</span>
                            </div>
                            ${tagsHtml}
                        </div>
                        <div class="sidebar-panel">
                            <div class="sidebar-panel-title">
                                Recent Commits
                                <span class="count">${info.commits.length}</span>
                            </div>
                            <div class="commit-list">${commitsHtml}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        app.innerHTML = `<div class="page-container"><div class="error">Repository not found or failed to load.</div></div>`;
    }
}

async function renderTree(name, ref, path) {
    try {
        const tree = await api(`/repos/${name}/tree/${ref}/${path}`);

        // Breadcrumb
        let breadcrumb = `<a href="#/${esc(name)}">${esc(name)}</a>`;
        if (path) {
            const parts = path.split('/').filter(Boolean);
            let accumulated = '';
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                accumulated += (accumulated ? '/' : '') + part;
                if (i === parts.length - 1) {
                    breadcrumb += `<span class="sep">/</span><span class="current">${esc(part)}</span>`;
                } else {
                    breadcrumb += `<span class="sep">/</span><a href="#/${esc(name)}/tree/${esc(ref)}/${esc(accumulated)}">${esc(part)}</a>`;
                }
            }
        }

        // File items
        const items = tree.items.map(item => {
            const icon = item.type === 'dir' ? 'folder' : 'description';
            const iconClass = item.type === 'dir' ? 'dir' : 'file';
            const itemPath = path ? `${path}/${item.name}` : item.name;
            const href = item.type === 'dir'
                ? `#/${esc(name)}/tree/${esc(ref)}/${esc(itemPath)}`
                : `#/${esc(name)}/blob/${esc(ref)}/${esc(itemPath)}`;

            const commitInfo = item.last_commit
                ? `<div class="file-commit-msg">${esc(item.last_commit.message)}</div>
                   <div class="file-date">${timeAgo(item.last_commit.date)}</div>`
                : `<div class="file-commit-msg"></div><div class="file-date"></div>`;

            return `
                <div class="file-item" onclick="window.location.href='${href}'">
                    <div class="file-icon ${iconClass}">
                        <span class="material-symbols-outlined">${icon}</span>
                    </div>
                    <div class="file-name"><a href="${href}">${esc(item.name)}</a></div>
                    ${commitInfo}
                </div>
            `;
        }).join('');

        app.innerHTML = `
            <div class="page-container">
                <div class="repo-header">
                    <div class="repo-header-title">
                        <span class="material-symbols-outlined">book</span>
                        <a href="#/${esc(name)}">${esc(name)}</a>
                    </div>
                </div>

                <div class="breadcrumb">${breadcrumb}</div>

                <div class="file-explorer">
                    <div class="file-explorer-header">
                        <div class="commit-info">
                            <span class="material-symbols-outlined" style="font-size:16px">account_tree</span>
                            <strong>${esc(ref)}</strong>
                        </div>
                    </div>
                    <ul class="file-list">
                        ${path ? `
                            <div class="file-item" onclick="window.location.href='#/${esc(name)}/tree/${esc(ref)}/${esc(tree.parent)}'">
                                <div class="file-icon dir">
                                    <span class="material-symbols-outlined">folder</span>
                                </div>
                                <div class="file-name"><a href="#/${esc(name)}/tree/${esc(ref)}/${esc(tree.parent)}">..</a></div>
                                <div class="file-commit-msg"></div>
                                <div class="file-date"></div>
                            </div>
                        ` : ''}
                        ${items}
                    </ul>
                </div>
            </div>
        `;
    } catch (err) {
        app.innerHTML = `<div class="page-container"><div class="error">Failed to load tree: ${esc(err.message)}</div></div>`;
    }
}

async function renderBlob(name, ref, path) {
    try {
        const blob = await api(`/repos/${name}/blob/${ref}/${path}`);

        // Breadcrumb
        let breadcrumb = `<a href="#/${esc(name)}">${esc(name)}</a>`;
        const parts = path.split('/').filter(Boolean);
        let accumulated = '';
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            accumulated += (accumulated ? '/' : '') + part;
            if (i === parts.length - 1) {
                breadcrumb += `<span class="sep">/</span><span class="current">${esc(part)}</span>`;
            } else {
                breadcrumb += `<span class="sep">/</span><a href="#/${esc(name)}/tree/${esc(ref)}/${esc(accumulated)}">${esc(part)}</a>`;
            }
        }

        if (blob.binary) {
            app.innerHTML = `
                <div class="page-container">
                    <div class="repo-header">
                        <div class="repo-header-title">
                            <span class="material-symbols-outlined">book</span>
                            <a href="#/${esc(name)}">${esc(name)}</a>
                        </div>
                    </div>
                    <div class="breadcrumb">${breadcrumb}</div>
                    <div class="file-explorer">
                        <div class="binary-notice">
                            Binary file (${formatSize(blob.size)})
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        const fileName = path.split('/').pop();
        const isMarkdown = fileName.toLowerCase().endsWith('.md');
        const lang = getLangFromPath(path);

        if (isMarkdown) {
            renderMarkdownBlob(name, ref, path, breadcrumb, blob, fileName);
        } else {
            renderCodeBlob(name, ref, path, breadcrumb, blob, fileName, lang);
        }
    } catch (err) {
        app.innerHTML = `<div class="page-container"><div class="error">File not found.</div></div>`;
    }
}

function getLangFromPath(path) {
    const ext = path.split('.').pop().toLowerCase();
    const map = {
        'js': 'javascript', 'jsx': 'javascript', 'mjs': 'javascript',
        'ts': 'typescript', 'tsx': 'typescript',
        'py': 'python', 'pyw': 'python',
        'sh': 'bash', 'bash': 'bash', 'zsh': 'bash',
        'json': 'json', 'jsonl': 'json',
        'yml': 'yaml', 'yaml': 'yaml',
        'toml': 'toml',
        'xml': 'xml', 'html': 'xml', 'htm': 'xml', 'svg': 'xml',
        'css': 'css', 'scss': 'css',
        'go': 'go',
        'rs': 'rust',
        'java': 'java',
        'sql': 'sql',
        'dockerfile': 'dockerfile',
        'md': 'markdown',
        'txt': 'plaintext',
        'cfg': 'ini', 'conf': 'ini', 'ini': 'ini',
    };
    // Check for Dockerfile specifically
    if (path.split('/').pop() === 'Dockerfile') return 'dockerfile';
    return map[ext] || 'plaintext';
}

function renderCodeBlob(name, ref, path, breadcrumb, blob, fileName, lang) {
    const lines = blob.content.split('\n');

    // Highlight with highlight.js
    let highlighted;
    if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
        try {
            highlighted = hljs.highlight(blob.content, { language: lang }).value;
        } catch {
            highlighted = esc(blob.content);
        }
    } else {
        highlighted = esc(blob.content);
    }

    // Split into lines for line numbers
    const highlightedLines = highlighted.split('\n');
    const lineNums = lines.map((_, i) => `<span class="ln">${i + 1}</span>`).join('');

    app.innerHTML = `
        <div class="page-container">
            <div class="repo-header">
                <div class="repo-header-title">
                    <span class="material-symbols-outlined">book</span>
                    <a href="#/${esc(name)}">${esc(name)}</a>
                </div>
            </div>
            <div class="breadcrumb">${breadcrumb}</div>
            <div class="file-explorer">
                <div class="file-header">
                    <span class="file-path">${esc(fileName)}</span>
                    <span class="file-info">${blob.line_count} lines · ${formatSize(blob.size)}</span>
                </div>
                <div class="code-viewer">
                    <div class="line-numbers-col">${lineNums}</div>
                    <pre class="code-content"><code class="hljs language-${esc(lang)}">${highlighted}</code></pre>
                </div>
            </div>
        </div>
    `;
}

function renderMarkdownBlob(name, ref, path, breadcrumb, blob, fileName) {
    // Render markdown
    const rendered = typeof marked !== 'undefined'
        ? marked.parse(blob.content)
        : `<pre>${esc(blob.content)}</pre>`;

    app.innerHTML = `
        <div class="page-container">
            <div class="repo-header">
                <div class="repo-header-title">
                    <span class="material-symbols-outlined">book</span>
                    <a href="#/${esc(name)}">${esc(name)}</a>
                </div>
            </div>
            <div class="breadcrumb">${breadcrumb}</div>
            <div class="file-explorer">
                <div class="file-header">
                    <span class="file-path">${esc(fileName)}</span>
                    <div class="file-header-actions">
                        <span class="file-info">${blob.line_count} lines</span>
                        <button class="btn btn-secondary btn-sm" id="md-toggle-btn" onclick="toggleMarkdownView()">
                            <span class="material-symbols-outlined">code</span>
                            Raw
                        </button>
                    </div>
                </div>
                <div id="md-rendered" class="markdown-body">${rendered}</div>
                <div id="md-raw" class="code-viewer" style="display:none">
                    <div class="line-numbers-col">${blob.content.split('\n').map((_, i) => `<span class="ln">${i + 1}</span>`).join('')}</div>
                    <pre class="code-content"><code>${esc(blob.content)}</code></pre>
                </div>
            </div>
        </div>
    `;
}

function toggleMarkdownView() {
    const rendered = document.getElementById('md-rendered');
    const raw = document.getElementById('md-raw');
    const btn = document.getElementById('md-toggle-btn');
    if (!rendered || !raw || !btn) return;

    const showingRaw = raw.style.display !== 'none';
    if (showingRaw) {
        raw.style.display = 'none';
        rendered.style.display = '';
        btn.innerHTML = '<span class="material-symbols-outlined">code</span> Raw';
    } else {
        rendered.style.display = 'none';
        raw.style.display = '';
        btn.innerHTML = '<span class="material-symbols-outlined">article</span> Rendered';
    }
}

async function renderCommits(name, ref) {
    try {
        const data = await api(`/repos/${name}/commits/${ref}`);

        const commits = data.commits.map(c => `
            <div class="commit-item">
                <div class="commit-message">${esc(c.message)}</div>
                <div class="commit-meta">
                    <span class="commit-hash">${esc(c.short_hash)}</span>
                    <span>${esc(c.author)}</span>
                    <span>${timeAgo(c.date)}</span>
                </div>
            </div>
        `).join('');

        app.innerHTML = `
            <div class="page-container">
                <div class="repo-header">
                    <div class="repo-header-title">
                        <span class="material-symbols-outlined">book</span>
                        <a href="#/${esc(name)}">${esc(name)}</a>
                    </div>
                </div>
                <div class="sidebar-panel" style="margin-bottom:var(--space-lg)">
                    <div class="sidebar-panel-title">
                        Commits on ${esc(ref)}
                        <span class="count">${data.commits.length}</span>
                    </div>
                    <div class="commit-list">${commits || '<div class="empty-state">No commits.</div>'}</div>
                </div>
            </div>
        `;
    } catch (err) {
        app.innerHTML = `<div class="page-container"><div class="error">Failed to load commits.</div></div>`;
    }
}

// --- Router ---

async function handleRoute() {
    const route = getRoute();
    const parts = route.split('/').filter(Boolean);

    app.innerHTML = `
        <div class="loading">
            <span class="material-symbols-outlined spinning">progress_activity</span>
        </div>
    `;

    // Update sidebar active state
    document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
    if (parts.length === 0) {
        document.querySelector('.sidebar-item[data-page="repos"]')?.classList.add('active');
    }

    if (parts.length === 0) {
        await renderRepoList();
    } else if (parts.length === 1) {
        await renderRepoDetail(parts[0]);
    } else if (parts[1] === 'tree') {
        const name = parts[0];
        const ref = parts[2] || 'HEAD';
        const path = parts.slice(3).join('/');
        await renderTree(name, ref, path);
    } else if (parts[1] === 'blob') {
        const name = parts[0];
        const ref = parts[2] || 'HEAD';
        const path = parts.slice(3).join('/');
        await renderBlob(name, ref, path);
    } else if (parts[1] === 'commits') {
        const name = parts[0];
        const ref = parts[2] || 'HEAD';
        await renderCommits(name, ref);
    } else {
        app.innerHTML = '<div class="page-container"><div class="error">Page not found.</div></div>';
    }
}

window.addEventListener('hashchange', handleRoute);
window.addEventListener('load', handleRoute);
