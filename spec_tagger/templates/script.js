document.addEventListener("DOMContentLoaded", () => {
  // Read the payload injected by Python
  const data = window.REPORT_DATA;

  if (!data) {
    document.getElementById("results-container").innerHTML =
      "<p class='meta-info'>Error: No report data found.</p>";
    return;
  }

  renderTestResults(data.test_results || {});
  renderInvalidTags(data.invalid_tags || []);
});

function renderTestResults(results) {
  const container = document.getElementById("results-container");
  const specItems = Object.entries(results);

  if (specItems.length === 0) {
    container.innerHTML = "<p class='meta-info'>No tests executed.</p>";
    return;
  }

  specItems.forEach(([specName, details]) => {
    const card = document.createElement("div");
    card.className = "card";

    // Determine overall status based on presence of failures or errors
    const hasFailures = details.Failures || details.Error;
    const statusClass = hasFailures ? "status-fail" : "status-pass";

    // Build the inner HTML template safely
    let htmlContent = `
            <h3>${escapeHtml(specName)}</h3>
            <div class="meta-info">
                <div>Line Number: ${details["Line Number"] || "N/A"}</div>
                <div>Execution Time: ${details["Execution Time"] || "N/A"}</div>
                <div>Test Coverage: ${details["Test Coverage"] || "N/A"}</div>
            </div>
            ${details["Spec snapshot"] ? `<strong>Snapshot:</strong><code class="code-snippet">${escapeHtml(details["Spec snapshot"])}</code>` : ""}
        `;

    // Append execution blocks dynamically
    if (details.Passes) {
      htmlContent += `
                <div class="status-block status-pass">
                    <strong>Passed</strong> 
                    <div>Coverage: ${details.Passes.Coverage || "N/A"}</div>
                </div>
            `;
    }

    if (details.Failures) {
      htmlContent += `
                <div class="status-block status-fail">
                    <strong>Failed</strong>
                    <code class="code-snippet">${escapeHtml(details.Failures.Output || "Unknown failure")}</code>
                </div>
            `;
    }

    if (details.Error) {
      htmlContent += `
                <div class="status-block status-fail">
                    <strong>Error</strong>
                    <code class="code-snippet">${escapeHtml(details.Error.Output || "Unknown error")}</code>
                </div>
            `;
    }

    card.innerHTML = htmlContent;
    container.appendChild(card);
  });
}

function renderInvalidTags(tags) {
  const container = document.getElementById("tags-container");

  // Handle both dictionaries or strings depending on how you stored the tag data
  if (Object.keys(tags).length === 0) {
    container.innerHTML = "<p class='meta-info'>No invalid tags found.</p>";
    return;
  }

  // Assuming tags is a dictionary where the key is the Tag and value is the Reason
  // Based on your schema: 
  // Invalid Tags
  //     Tag
  //         Reason
  for (const [tagName, reason] of Object.entries(tags)) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
            <h3 style="color: var(--warning)">${escapeHtml(tagName)}</h3>
            <p><strong>Reason:</strong> ${escapeHtml(reason)}</p>
        `;
    container.appendChild(card);
  }
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
