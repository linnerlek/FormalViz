// Lambda resizable divider
function initializeLambdaResizableDivider() {
  const divider = document.getElementById("divider");
  const leftSection = document.querySelector(".lambda-left-section");
  const rightSection = document.querySelector(".lambda-right-section");
  const container = document.getElementById("app-container");

  // Only run if all elements exist and are visible
  if (!divider || !leftSection || !rightSection || !container) {
    setTimeout(initializeLambdaResizableDivider, 100);
    return;
  }

  // Prevent double-binding if both RAViz and Lambda are present
  if (divider.hasAttribute("data-lambda-resize")) return;
  divider.setAttribute("data-lambda-resize", "true");

  let isDragging = false;

  divider.addEventListener("mousedown", (e) => {
    // Only activate if lambda sections are present
    if (!leftSection || !rightSection) return;
    isDragging = true;
    document.body.style.cursor = "ew-resize";
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const containerWidth = container.offsetWidth;
    const leftWidth = e.clientX - container.getBoundingClientRect().left;
    if (leftWidth >= 300 && leftWidth <= containerWidth - 100) {
      leftSection.style.flexBasis = `${leftWidth}px`;
      rightSection.style.flexBasis = `${containerWidth - leftWidth}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.cursor = "default";
  });
}

document.addEventListener("DOMContentLoaded", initializeLambdaResizableDivider);
document.addEventListener("DOMContentLoaded", function () {
  const schemaContainer = document.getElementById("schema-container");

  if (schemaContainer) {
    const schemaSummary = schemaContainer.querySelector("summary");

    schemaSummary.addEventListener("click", function () {
      schemaContainer.open = !schemaContainer.open;
    });
  }
});

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    togglePaginationButtons: function (rowCount) {
      const prevButton = document.getElementById("prev-page-btn");
      const nextButton = document.getElementById("next-page-btn");

      if (rowCount > 8) {
        prevButton.style.display = "inline-block";
        nextButton.style.display = "inline-block";
      } else {
        prevButton.style.display = "none";
        nextButton.style.display = "none";
      }
      return null;
    },
  },
});

function observeCytoscapeTree() {
  const cyElement = document.getElementById("cytoscape-tree");

  if (cyElement) {
    const resizeObserver = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        if (window.cy) {
          cy.resize();
          cy.center();
          cy.fit();
        }
      });
    });
    resizeObserver.observe(cyElement);
  } else {
    console.log("Waiting for 'cytoscape-tree' to load...");
    setTimeout(observeCytoscapeTree, 100);
  }
}

document.addEventListener("DOMContentLoaded", observeCytoscapeTree);

function initializeResizableDivider() {
  const divider = document.getElementById("divider");
  const leftSection = document.getElementById("left-section");
  const rightSection = document.getElementById("right-section");
  const container = document.getElementById("app-container");

  // Check if elements exist
  if (!divider || !leftSection || !rightSection || !container) {
    console.log("Waiting for elements to load...");
    setTimeout(initializeResizableDivider, 100);
    return;
  }

  let isDragging = false;

  divider.addEventListener("mousedown", (e) => {
    isDragging = true;
    document.body.style.cursor = "ew-resize";
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const containerWidth = container.offsetWidth;
    const leftWidth = e.clientX;

    if (leftWidth >= 450 && leftWidth <= containerWidth - 50) {
      leftSection.style.flexBasis = `${leftWidth}px`;
      rightSection.style.flexBasis = `${containerWidth - leftWidth}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.cursor = "default";
  });
}

document.addEventListener("DOMContentLoaded", initializeResizableDivider);

function initializeTreeTableResizableDivider() {
  const divider = document.getElementById("tree-table-divider");
  const treeSection = document.getElementById("cytoscape-tree");
  const tableSection = document.querySelector(".table-and-pagination");
  const container = document.querySelector(".tree-table-container");

  if (!divider || !treeSection || !tableSection || !container) {
    setTimeout(initializeTreeTableResizableDivider, 100);
    return;
  }

  let isDragging = false;
  let startX = 0;
  let startTreeWidth = 0;

  divider.addEventListener("mousedown", (e) => {
    isDragging = true;
    startX = e.clientX;
    startTreeWidth = treeSection.getBoundingClientRect().width;
    document.body.style.cursor = "ew-resize";
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const deltaX = e.clientX - startX;
    const newTreeWidth = startTreeWidth + deltaX;

    const containerWidth = container.getBoundingClientRect().width;

    if (newTreeWidth >= 10 && newTreeWidth <= containerWidth - 10) {
      treeSection.style.flexBasis = `${newTreeWidth}px`;
      tableSection.style.flexBasis = `${containerWidth - newTreeWidth}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.cursor = "default";
  });
}

document.addEventListener(
  "DOMContentLoaded",
  initializeTreeTableResizableDivider
);

function initializeDatalogTreeTableResizableDivider() {
  const divider = document.getElementById("datalog-tree-table-divider");
  const treeSection = document.getElementById("datalog-graph");
  const tableSection = document.querySelector(
    ".datalog-tree-table-container .table-and-pagination"
  );
  const container = document.querySelector(".datalog-tree-table-container");

  if (!divider || !treeSection || !tableSection || !container) {
    setTimeout(initializeDatalogTreeTableResizableDivider, 100);
    return;
  }

  let isDragging = false;

  divider.addEventListener("mousedown", (e) => {
    isDragging = true;
    document.body.style.cursor = "ew-resize";
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const containerWidth = container.offsetWidth;
    const containerRect = container.getBoundingClientRect();
    const leftWidth = e.clientX - containerRect.left;
    const dividerWidth = 2; // Fixed divider width

    if (leftWidth >= 100 && leftWidth <= containerWidth - 100) {
      // Use width and flex: none instead of flex-basis
      treeSection.style.setProperty("flex", "none", "important");
      treeSection.style.setProperty(
        "width",
        `${leftWidth - dividerWidth / 2}px`,
        "important"
      );

      // Keep divider visible and fixed
      divider.style.setProperty("flex", "none", "important");
      divider.style.setProperty("width", `${dividerWidth}px`, "important");
      divider.style.setProperty("order", "1", "important");

      tableSection.style.setProperty("flex", "none", "important");
      tableSection.style.setProperty(
        "width",
        `${containerWidth - leftWidth - dividerWidth / 2}px`,
        "important"
      );
      tableSection.style.setProperty("order", "2", "important");

      // Trigger cytoscape resize and re-center after a short delay
      setTimeout(() => {
        const cyElement = document.getElementById("datalog-graph");
        if (cyElement && cyElement._cyreg && cyElement._cyreg.cy) {
          const cy = cyElement._cyreg.cy;
          cy.resize();
          cy.fit();
          cy.center();
        }
      }, 50);
    }
  });

  document.addEventListener("mouseup", () => {
    // Only center if we were actually dragging the divider
    const wasDragging = isDragging;
    isDragging = false;
    document.body.style.cursor = "default";

    // Final resize and center after divider dragging is complete
    if (wasDragging) {
      setTimeout(() => {
        const cyElement = document.getElementById("datalog-graph");
        if (cyElement && cyElement._cyreg && cyElement._cyreg.cy) {
          const cy = cyElement._cyreg.cy;
          cy.resize();
          cy.fit();
          cy.center();
        }
      }, 100);
    }
  });
}

document.addEventListener(
  "DOMContentLoaded",
  initializeDatalogTreeTableResizableDivider
);

// Function to center and fit the datalog graph
function centerDatalogGraph() {
  const cyElement = document.getElementById("datalog-graph");
  if (cyElement && cyElement._cyreg && cyElement._cyreg.cy) {
    const cy = cyElement._cyreg.cy;
    // Use a short timeout to ensure elements are rendered
    setTimeout(() => {
      cy.resize();
      cy.fit();
      cy.center();
    }, 100);
  }
}

// Make the function globally available for Dash callbacks
window.centerDatalogGraph = centerDatalogGraph;
