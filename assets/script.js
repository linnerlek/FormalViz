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
        togglePaginationButtons: function(rowCount) {
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
        }
    }
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



