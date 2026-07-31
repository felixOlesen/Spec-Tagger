document.addEventListener("DOMContentLoaded", () => {
  // Read the payload injected by Python
  const data = window.REPORT_DATA;

  if (!data) {
    document.getElementById("results-container").innerHTML =
      "<p class='meta-info'>Error: No report data found.</p>";
    return;
  }
  if (data.one_by_one) {
    document.getElementById("one-by-one-header").innerHTML = "<em>One-by-one Mode</em>";
  }
  renderTestResults(data.test_results || {}, data.one_by_one || false);
  renderInvalidTags(data.invalid_tags || []);
});

function renderTestResults(results, one_by_one) {
  const container = document.getElementById("results-container");
  const specItems = Object.entries(results);

  if (specItems.length === 0) {
    container.innerHTML = "<p class='meta-info'>No tests executed.</p>";
    return;
  }

  let rowsHtml = "";

  specItems.forEach(([specName, details], specIndex) => {
    const specTag = details.spec_tag || {};
    const testTags = details.test_tags || [];
    const passCount = details.pass_count ?? 0;
    var testCount = details.test_count ?? 0;
    const runs = details.results || [];
    const rowId = `spec-${specIndex}-detail`;
    const canExpand = runs.length > 0;

    const linkedTestsHtml = testTags.length > 0
      ? `<ul class="linked-tests">${testTags
        .map(t => `<li>${escapeHtml(t.filename)}${t.test_function ? ` :: ${escapeHtml(t.test_function)}` : ""}</li>`)
        .join("")}</ul>`
      : `<span class="meta-info">None</span>`;

    let overallClass = "badge-untested";
    if (testCount > 0) {
      if (one_by_one == true) {
        overallClass = passCount === testCount ? "badge-pass" : "badge-fail";
      } else {
        testCount = 1
        overallClass = passCount === testCount ? "badge-pass" : "badge-fail";
      }
    }

    // One dot per test run, so a spec with many results stays a single row.
    const outcomesHtml = canExpand
      ? runs
        .map(run => `<span class="outcome-dot outcome-${escapeHtml(run.outcome)}" title="${escapeHtml(run.cmd || run.outcome)}"></span>`)
        .join("")
      : `<span class="meta-info">No linked tests ran</span>`;

    rowsHtml += `
      <tr class="spec-row${canExpand ? " expandable" : ""}" ${canExpand ? `data-target="${rowId}"` : ""}>
        <td>
          <div class="spec-name">${canExpand ? `<span class="chevron">&#9656;</span>` : ""}${escapeHtml(specName)}</div>
          <div class="meta-info">${escapeHtml(specTag.filename || "N/A")}:${escapeHtml(String(specTag.line ?? "N/A"))}</div>
        </td>
        <td>${linkedTestsHtml}</td>
        <td>
          <div><span class="badge ${overallClass}">${passCount}/${testCount} passed</span></div>
          <div class="meta-info">Exec Time: ${escapeHtml(details.exec_time || "N/A")}</div>
          <div class="meta-info">Date/Time: ${escapeHtml(details.test_date || "N/A")}</div>
        </td>
        <td class="outcomes-cell">${outcomesHtml}</td>
      </tr>
    `;

    if (canExpand) {
      const runsHtml = runs
        .map(
          run => `
            <tr class="run-row">
              <td><span class="badge badge-${escapeHtml(run.outcome)}">${escapeHtml(run.outcome)}</span></td>
              <td class="cmd-cell">${run.cmd ? `<code class="code-inline">${escapeHtml(run.cmd)}</code>` : "&mdash;"}</td>
              <td>
                ${run.output ? `<strong>Output</strong><code class="code-snippet">${escapeHtml(run.output)}</code>` : ""}
                ${run.error ? `<strong>Error</strong><code class="code-snippet">${escapeHtml(run.error)}</code>` : ""}
                ${!run.output && !run.error ? "&mdash;" : ""}
              </td>
            </tr>
          `
        )
        .join("");

      rowsHtml += `
        <tr id="${rowId}" class="detail-row hidden">
          <td colspan="4">
            <table class="run-table">
              <thead><tr><th>Outcome</th><th>Command</th><th>Output / Error</th></tr></thead>
              <tbody>${runsHtml}</tbody>
            </table>
          </td>
        </tr>
      `;
    }
  });

  container.innerHTML = `
    <table class="report-table">
      <thead>
        <tr>
          <th>Spec Tag</th>
          <th>Linked Tests</th>
          <th>Summary</th>
          <th>Outcomes</th>
        </tr>
      </thead>
      <tbody>${rowsHtml}</tbody>
    </table>
  `;

  container.addEventListener("click", event => {
    const row = event.target.closest(".spec-row.expandable");
    if (!row) return;
    const target = document.getElementById(row.dataset.target);
    if (!target) return;
    target.classList.toggle("hidden");
    row.classList.toggle("expanded");
  });
}

function renderInvalidTags(tags) {
  const container = document.getElementById("tags-container");

  if (!tags || Object.keys(tags).length === 0) {
    container.innerHTML = "<p class='meta-info'>No invalid tags found.</p>";
    return;
  }

  const rowsHtml = Object.values(tags)
    .map(
      tag_data => `
        <tr>
          <td class="warning-text">${escapeHtml(tag_data["full_tag"])}</td>
          <td>${escapeHtml(tag_data["filename"])}</td>
          <td>${escapeHtml(String(tag_data["line"]))}</td>
          <td>${escapeHtml(tag_data["validity"]["reasons"])}</td>
        </tr>
      `
    )
    .join("");

  container.innerHTML = `
    <table class="report-table">
      <thead>
        <tr>
          <th>Tag</th>
          <th>File</th>
          <th>Line</th>
          <th>Reason</th>
        </tr>
      </thead>
      <tbody>${rowsHtml}</tbody>
    </table>
  `;
}

// Utility function to prevent XSS if test outputs contain raw HTML
function escapeHtml(unsafe) {
  if (typeof unsafe !== 'string') return unsafe;
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
