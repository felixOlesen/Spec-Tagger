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
  console.log(specItems);

  if (specItems.length === 0) {
    container.innerHTML = "<p class='meta-info'>No tests executed.</p>";
    return;
  }

  specItems.forEach(([specName, details]) => {
    const card = document.createElement("div");
    card.className = "card";

    // Determine overall status based on presence of failures or errors
    const test_result = details.result;

    var test_function_names = ``
    details.test_tags.forEach(
      tag => {
        test_function_names += `<li>${tag.filename} : ${tag.test_function}</li>`
      }
    )

    console.log(test_function_names)
    // Build the inner HTML template safely
    let htmlContent = `
            <h3>${escapeHtml(specName)}</h3>
            <div class="meta-info">
                <div>Spec File: ${details.spec_tag.filename || "N/A"}</div>
                <div>Line Number: ${details.spec_tag.line || "N/A"}</div>
                <div>Execution Time: ${details.exec_time || "N/A"}</div>
                <div>Test Count: ${details.test_count || "N/A"}</div>
                <div>Tests: <ul> ${test_function_names} </ul> </div> 
            </div>
            ${details["Spec snapshot"] ? `<strong>Snapshot:</strong><code class="code-snippet">${escapeHtml(details["Spec snapshot"])}</code>` : ""}
        `;

    // Append execution blocks dynamically
    if (test_result == "passed") {
      htmlContent += `
                <div class="status-block status-pass">
                    <strong>Passed</strong> 
                    <div>Coverage: ${"N/A"}</div>
                </div>
            `;
    }

    if (test_result == "failed") {
      htmlContent += `
                <div class="status-block status-fail">
                    <strong>Failed</strong>
                    <code class="code-snippet">${escapeHtml(details.output || "Unknown failure")}</code>
                </div>
            `;
    }

    if (details.error) {
      htmlContent += `
                <div class="status-block status-fail">
                    <strong>Error</strong>
                    <code class="code-snippet">${escapeHtml(details.error || "Unknown error")}</code>
                </div>
            `;
    }

    card.innerHTML = htmlContent;
    container.appendChild(card);
  });
}

function renderInvalidTags(tags) {
  const container = document.getElementById("tags-container");
  console.log(tags[0])
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

  for (const [index, tag_data] of Object.entries(tags)) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `<h3 style="color: var(--warning)">${escapeHtml(tag_data['tag'])}</h3>`;
    card.innerHTML += `<p>${escapeHtml(tag_data['file'])}:${escapeHtml(tag_data['line'])}</p>`;
    card.innerHTML += `<p><strong>Reason:</strong> ${escapeHtml(tag_data['reason'])}</p>`;
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
