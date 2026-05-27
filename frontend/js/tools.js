const toolNames = {
  hand: "Рука",
  brush: "Кисть",
  eraser: "Ластик",
};

function clearToolInteractions() {
  if (drawInteraction) {
    map.removeInteraction(drawInteraction);
    drawInteraction = null;
  }

  if (selectInteraction) {
    map.removeInteraction(selectInteraction);
    selectInteraction = null;
  }

  if (modifyInteraction) {
    map.removeInteraction(modifyInteraction);
    modifyInteraction = null;
  }
}

function enableHandMode() {
  clearToolInteractions();

  modifyInteraction = new ol.interaction.Modify({
    source: source,
    style: createModifyStyle(),
  });

  modifyInteraction.on("modifyend", () => {
  if (typeof markRouteAsChanged === "function") {
    markRouteAsChanged();
  }
});

  map.addInteraction(modifyInteraction);
}

function enableBrushMode() {
  clearToolInteractions();

  drawInteraction = new ol.interaction.Draw({
    source: source,
    type: "LineString",
    style: () => createLineStyle(),
  });

  drawInteraction.on("drawend", (event) => {
  if (typeof getEditingRouteId === "function") {
    event.feature.set("routeId", getEditingRouteId());
  }

  if (typeof markRouteAsChanged === "function") {
    setTimeout(markRouteAsChanged, 0);
  }

  if (typeof snapCurrentEditingRoute === "function") {
    setTimeout(snapCurrentEditingRoute, 0);
  }
});

  map.addInteraction(drawInteraction);
}

function enableEraserMode() {
  clearToolInteractions();

  selectInteraction = new ol.interaction.Select({
    condition: ol.events.condition.singleClick,
    layers: [vectorLayer],
    style: null,
  });

  selectInteraction.on("select", (event) => {
    if (!event.selected.length) return;

    event.selected.forEach((feature) => {
      source.removeFeature(feature);
    });

    if (typeof markRouteAsChanged === "function") {
      markRouteAsChanged();
    }

    selectInteraction.getFeatures().clear();
  });

  map.addInteraction(selectInteraction);
}

function setTool(tool) {
  activeTool = tool;
  activeToolText.textContent = toolNames[tool];

  if (tool === "hand") enableHandMode();
  if (tool === "brush") enableBrushMode();
  if (tool === "eraser") enableEraserMode();
}
